from langgraph.graph import StateGraph, MessagesState, START, END
from langgraph.checkpoint.memory import MemorySaver
from langgraph.prebuilt import ToolNode
from langchain_ollama import ChatOllama
from langchain_core.messages import SystemMessage, AIMessage
from langchain_core.tools import tool
from prompts.orchestrator_prompt import ORCHESTRATOR_SYSTEM_PROMPT

from tools.rag import rag_search
from tools.pdf import pdf_tool

import json

# ---- Mechanism 1: real tools, orchestrator calls these directly ----
@tool
def read_file(path: str) -> str:
    """Read the contents of a local file."""
    return "[Tool 'read_file' is in development]"

@tool
def write_file(path: str, content: str) -> str:
    """Write content to a local file."""
    return "[Tool 'write_file' is in development]"

tools = [read_file, write_file, rag_search, pdf_tool]
tool_node = ToolNode(tools)

llm = ChatOllama(model="qwen2.5:7b-instruct")
llm_with_tools = llm.bind_tools(tools)

# ---- Mechanism 2: delegation to vision/code, via JSON in plain response ----
def parse_delegation(content: str):
    try:
        parsed = json.loads(content)
        if isinstance(parsed, dict) and parsed.get("action") in ("vision", "code"):
            return parsed
    except (json.JSONDecodeError, TypeError):
        return None
    return None

def rerouter_stub(state: MessagesState):
    last = state["messages"][-1]
    delegation = parse_delegation(last.content)
    action = delegation["action"] if delegation else "unknown"

    if action == "code":
        # ollama_client.route_to_specialist generates the code (loading the
        # coding model via the rerouter's residency rules), tools/code/code.py
        # then executes the generated code string.
        from tools.code.code import execute_code
        from tools.code.code_prompt import build_code_prompt, extract_code_block
        from ollama_client import route_to_specialist

        task_description = delegation.get("task", last.content) if delegation else last.content
        prompt = build_code_prompt(task_description)
        specialist_response = route_to_specialist("code", [{"role": "user", "content": prompt}])
        raw_content = specialist_response["message"]["content"]
        code_string = extract_code_block(raw_content)

        result = execute_code(code_string)
        return {"messages": [AIMessage(content=json.dumps(result))]}

    if action == "vision":
        # Reuse the same VisionTool singleton (memory + backend) that
        # tools/Vision/vision_module/router.py exposes over HTTP, so images
        # uploaded via /tools/vision/upload are visible here too.
        from tools.Vision.vision_module.router import tool as vision_tool
        from tools.Vision.vision_module.schemas import VisionRequest

        session_id = delegation.get("session_id", "default") if delegation else "default"
        query = delegation.get("query", last.content) if delegation else last.content

        request = VisionRequest(session_id=session_id, action="vision", payload={"query": query})
        result = vision_tool.handle(request)
        return {"messages": [AIMessage(content=result.model_dump_json())]}

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