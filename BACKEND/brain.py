import json
import logging
import os
import re
import httpx

from langchain_core.messages import AIMessage, SystemMessage
from langchain_core.tools import tool
from langchain_ollama import ChatOllama
from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import END, START, MessagesState, StateGraph
from langgraph.prebuilt import ToolNode

from prompts.orchestrator_prompt import ORCHESTRATOR_SYSTEM_PROMPT
from tools.pdf import pdf_tool
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

tools = [read_file, write_file, rag_search, pdf_tool]
tool_node = ToolNode(tools)

llm = ChatOllama(model=ORCHESTRATOR_MODEL)
llm_with_tools = llm.bind_tools(tools)

# ---- Mechanism 2: delegation to vision/code, via JSON in plain response ----
def parse_delegation(content: str):
    """
    Robust delegation parser:
    Handles raw JSON, markdown ```json codeblocks, and embedded JSON objects.
    """
    if not content or not isinstance(content, str):
        return None

    # 1. Direct JSON parse
    try:
        parsed = json.loads(content.strip())
        if isinstance(parsed, dict) and parsed.get("action") in ("vision", "code"):
            return parsed
    except (json.JSONDecodeError, TypeError):
        pass

    # 2. Extract from markdown codeblock (```json ... ``` or ``` ...)
    code_block_match = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", content, re.DOTALL)
    if code_block_match:
        try:
            parsed = json.loads(code_block_match.group(1).strip())
            if isinstance(parsed, dict) and parsed.get("action") in ("vision", "code"):
                return parsed
        except (json.JSONDecodeError, TypeError):
            pass

    # 3. Find any embedded JSON object containing "action": "vision" or "code"
    embedded_match = re.search(r"\{[^{}]*\"action\"\s*:\s*\"(vision|code)\"[^{}]*\}", content, re.DOTALL)
    if embedded_match:
        try:
            parsed = json.loads(embedded_match.group(0).strip())
            if isinstance(parsed, dict) and parsed.get("action") in ("vision", "code"):
                return parsed
        except (json.JSONDecodeError, TypeError):
            pass

    return None

def rerouter_stub(state: MessagesState):
    last = state["messages"][-1]
    delegation = parse_delegation(last.content)
    action = delegation["action"] if delegation else "unknown"

    if action == "code":
        from tools.code.code import execute_code
        from tools.code.code_prompt import build_code_prompt, extract_code_block
        from ollama_client import route_to_specialist

        task_description = delegation.get("task", last.content) if delegation else last.content
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
            return {"messages": [AIMessage(content=summary)]}
        except Exception as e:
            logger.error("Coding specialist execution failed: %s", e)
            return {"messages": [AIMessage(content=f"[Coding specialist error: {e}]")]}

    if action == "vision":
        from tools.Vision.vision_module.router import tool as vision_tool
        from tools.Vision.vision_module.schemas import VisionRequest

        session_id = delegation.get("session_id", "default") if delegation else "default"
        query = delegation.get("query", last.content) if delegation else last.content

        try:
            request = VisionRequest(session_id=session_id, action="vision", payload={"query": query})
            result = vision_tool.handle(request)
            return {"messages": [AIMessage(content=result.model_dump_json())]}
        except Exception as e:
            logger.error("Vision specialist execution failed: %s", e)
            return {"messages": [AIMessage(content=f"[Vision specialist error: {e}]")]}

    return {"messages": [AIMessage(content=f"[{action.capitalize()} specialist is in development]")]}

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