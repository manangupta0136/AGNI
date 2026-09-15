import json
import logging
import os
import re
import httpx

from langchain_core.messages import AIMessage, HumanMessage, SystemMessage
from langchain_core.tools import tool
from langchain_ollama import ChatOllama
from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import END, START, MessagesState, StateGraph
from langgraph.prebuilt import ToolNode

from prompts.orchestrator_prompt import ORCHESTRATOR_SYSTEM_PROMPT
from tools.pdf import pdf_tool, read_pdf_tool, docx_tool, pptx_tool
from tools.rag import rag_search

logger = logging.getLogger("agni.brain")

# ---- Dynamic Orchestrator Model Resolution ----
def get_best_orchestrator_model() -> str:
    preferred = os.getenv("AGNI_ORCHESTRATOR_MODEL", "qwen2.5:7b-instruct")
    try:
        resp = httpx.get("http://localhost:11434/api/tags", timeout=2.0)
        if resp.status_code == 200:
            installed = [m.get("name") for m in resp.json().get("models", [])]
            if preferred in installed:
                return preferred
            # If preferred not found, choose best match or first installed
            for candidate in ["qwen2.5:7b-instruct", "mistral:latest", "llama3.1:8b", "deepseek-r1:1.5b"]:
                if candidate in installed:
                    return candidate
            if installed:
                return installed[0]
    except Exception as e:
        logger.debug("Ollama model check failed: %s", e)
    return preferred

ORCHESTRATOR_MODEL = get_best_orchestrator_model()
logger.info("Brain orchestrator initialized with model: %s", ORCHESTRATOR_MODEL)

# ---- Mechanism 1: real tools, orchestrator calls these directly ----
@tool
def read_file(path: str) -> str:
    """Read the contents of a local file."""
    try:
        with open(path, "r", encoding="utf-8") as f:
            return f.read()
    except Exception as e:
        return f"[Error reading file {path}: {e}]"

@tool
def write_file(path: str, content: str) -> str:
    """Write content to a local file."""
    try:
        with open(path, "w", encoding="utf-8") as f:
            f.write(content)
        return f"[Successfully wrote {len(content)} characters to {path}]"
    except Exception as e:
        return f"[Error writing file {path}: {e}]"

tools = [read_file, write_file, rag_search, pdf_tool, read_pdf_tool, docx_tool, pptx_tool]
tool_node = ToolNode(tools)

llm = ChatOllama(model=ORCHESTRATOR_MODEL)
llm_with_tools = llm.bind_tools(tools)

def _find_balanced_json_objects(content: str):
    """
    Scan content for top-level {...} spans using brace-depth counting (not
    regex), so nested objects/arrays inside the JSON — e.g. an "stm" array
    full of {"role": ..., "content": ...} turns — don't break extraction.
    Yields each balanced top-level object substring found, outermost first.
    """
    depth = 0
    start = None
    in_string = False
    escape = False
    for i, ch in enumerate(content):
        if in_string:
            if escape:
                escape = False
            elif ch == "\\":
                escape = True
            elif ch == '"':
                in_string = False
            continue
        if ch == '"':
            in_string = True
        elif ch == "{":
            if depth == 0:
                start = i
            depth += 1
        elif ch == "}":
            if depth > 0:
                depth -= 1
                if depth == 0 and start is not None:
                    yield content[start:i + 1]
                    start = None


# ---- Mechanism 2: delegation to vision/code, via JSON in plain response ----
def parse_delegation(content: str):
    """
    Robust delegation parser:
    Handles raw JSON, markdown ```json codeblocks, and embedded JSON objects
    — including ones containing nested objects/arrays (e.g. a populated
    "stm" field), and ones preceded/followed by prose the model added
    despite being told not to.
    """
    if not content or not isinstance(content, str):
        return None

    # 1. Direct JSON parse of the whole trimmed content
    try:
        parsed = json.loads(content.strip())
        if isinstance(parsed, dict) and parsed.get("action") in ("vision", "code"):
            return parsed
    except (json.JSONDecodeError, TypeError):
        pass

    # 2. Extract from markdown codeblock (```json ... ``` or ``` ...)
    code_block_match = re.search(r"```(?:json)?\s*(\{.*\})\s*```", content, re.DOTALL)
    if code_block_match:
        try:
            parsed = json.loads(code_block_match.group(1).strip())
            if isinstance(parsed, dict) and parsed.get("action") in ("vision", "code"):
                return parsed
        except (json.JSONDecodeError, TypeError):
            pass

    # 3. Scan for any balanced top-level JSON object anywhere in the text
    #    (handles nested braces/arrays and surrounding prose).
    for candidate in _find_balanced_json_objects(content):
        try:
            parsed = json.loads(candidate)
        except (json.JSONDecodeError, TypeError):
            continue
        if isinstance(parsed, dict) and parsed.get("action") in ("vision", "code"):
            return parsed

    return None

# Matches the path out of "... (local path: /some/dir/My Photo (1).jpg)" —
# stop at the LAST ")" on the line, not the first non-space run, since real
# filenames (screenshots, camera exports) routinely contain spaces.
ATTACHMENT_PATH_RE = re.compile(r"local path:\s*(.+?)\)\s*(?:\n|$)")
IMAGE_EXTENSIONS = (".png", ".jpg", ".jpeg", ".gif", ".bmp", ".webp", ".tif", ".tiff")


def _find_attached_image_paths(text: str) -> list[str]:
    return [
        p for p in ATTACHMENT_PATH_RE.findall(text)
        if p.lower().endswith(IMAGE_EXTENSIONS)
    ]


_SPECIALIST_RESULT_PREFIX = "[SYSTEM: specialist tool result below — not from the user]"


def _last_human_message_content(state: MessagesState, exclude: object = None) -> str:
    """Find the most recent actual user message in the conversation, skipping
    the delegation AIMessage itself and any synthetic specialist-result
    messages injected by _specialist_result_message. Used when the model's
    delegation JSON doesn't include a "query"/"task" field of its own (it's
    often just {"action": "vision"} plus a stale/empty "stm")."""
    for msg in reversed(state["messages"]):
        if msg is exclude:
            continue
        if isinstance(msg, HumanMessage) or getattr(msg, "type", None) == "human":
            if isinstance(msg.content, str) and msg.content.startswith(_SPECIALIST_RESULT_PREFIX):
                continue
            return msg.content
    return exclude.content if exclude is not None else ""


def _specialist_result_message(content: str) -> HumanMessage:
    """
    Wrap a specialist/tool result as a HumanMessage rather than an
    AIMessage. rerouter_stub's output feeds straight back into chatbot_node
    (edge: rerouter -> chatbot), which immediately calls the LLM again. If
    the result were appended as another AIMessage, the message history would
    end in two consecutive assistant turns with no human turn between them
    — most chat templates (including Ollama's) treat that as the assistant
    having already replied, and frequently answer with an empty completion.
    Framing it as a (clearly labeled, non-user) human-role turn keeps the
    conversation alternating properly so the model actually generates a
    real text reply summarizing the result.
    """
    return HumanMessage(
        content=f"[SYSTEM: specialist tool result below — not from the user]\n\n{content}"
    )


def rerouter_stub(state: MessagesState, config: dict = None):
    last = state["messages"][-1]
    delegation = parse_delegation(last.content)
    action = delegation["action"] if delegation else "unknown"
    thread_id = ((config or {}).get("configurable") or {}).get("thread_id", "default")
    user_query = _last_human_message_content(state, exclude=last)

    if action == "code":
        from tools.code.code import execute_code
        from tools.code.code_prompt import build_code_prompt, extract_code_block
        from ollama_client import route_to_specialist

        task_description = delegation.get("task") if delegation else None
        task_description = task_description or user_query
        prompt = build_code_prompt(task_description)
        try:
            specialist_response = route_to_specialist("code", [{"role": "user", "content": prompt}])
            raw_content = specialist_response["message"]["content"]
            code_string = extract_code_block(raw_content)
            result = execute_code(code_string)
            summary = (
                f"### [Code Execution Specialist]\n\n"
                f"```python\n{code_string}\n```\n\n"
                f"**Output:**\n```\n{result.get('output', '')}\n```"
            )
            return {"messages": [_specialist_result_message(summary)]}
        except Exception as e:
            logger.error("Coding specialist execution failed: %s", e)
            return {"messages": [_specialist_result_message(f"[Coding specialist error: {e}]")]}

    if action == "vision":
        from tools.Vision.vision_module.router import tool as vision_tool
        from tools.Vision.vision_module.schemas import VisionRequest

        # session_id must match whatever the image was registered under, so
        # use the conversation's own thread_id rather than trusting the
        # model to invent/echo a session_id in its delegation JSON.
        session_id = thread_id
        query = (delegation.get("query") if delegation else None) or user_query

        # The attachment path lives in the conversation text (the
        # "[ATTACHED FILES]" block main.py prepends), not in the vision
        # tool's own short-term image memory yet — register any newly
        # attached images for this session before asking it to analyze one.
        image_paths = []
        for msg in state["messages"]:
            content = getattr(msg, "content", "")
            if isinstance(content, str):
                image_paths.extend(_find_attached_image_paths(content))
        if image_paths:
            vision_tool.register_new_images(session_id, list(dict.fromkeys(image_paths)))

        try:
            request = VisionRequest(session_id=session_id, action="vision", payload={"query": query})
            result = vision_tool.handle(request)
            return {"messages": [_specialist_result_message(result.model_dump_json())]}
        except Exception as e:
            logger.error("Vision specialist execution failed: %s", e)
            return {"messages": [_specialist_result_message(f"[Vision specialist error: {e}]")]}

    return {"messages": [_specialist_result_message(f"[{action.capitalize()} specialist is in development]")]}

def chatbot_node(state: MessagesState):
    messages = state["messages"]
    if not any(isinstance(m, SystemMessage) for m in messages):
        messages = [SystemMessage(content=ORCHESTRATOR_SYSTEM_PROMPT)] + messages
    response = llm_with_tools.invoke(messages)
    return {"messages": [response]}

def route_after_chatbot(state: MessagesState):
    last = state["messages"][-1]
    if getattr(last, "tool_calls", None):
        return "tools"
    if parse_delegation(last.content):
        return "rerouter"
    return "end"

builder = StateGraph(MessagesState)
builder.add_node("chatbot", chatbot_node)
builder.add_node("tools", tool_node)
builder.add_node("rerouter", rerouter_stub)

builder.add_edge(START, "chatbot")
builder.add_conditional_edges(
    "chatbot",
    route_after_chatbot,
    {"tools": "tools", "rerouter": "rerouter", "end": END}
)
builder.add_edge("tools", "chatbot")
builder.add_edge("rerouter", "chatbot")

memory = MemorySaver()
graph = builder.compile(checkpointer=memory)