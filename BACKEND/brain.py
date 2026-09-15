import logging
import os
import re
import threading
import time
from typing import Optional

import httpx

from langchain_core.messages import AIMessage, HumanMessage, SystemMessage, ToolMessage
from langchain_core.tools import tool
from langchain_ollama import ChatOllama
from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import END, START, MessagesState, StateGraph
from langgraph.prebuilt import ToolNode

from prompts.orchestrator_prompt import ORCHESTRATOR_SYSTEM_PROMPT
from tools.pdf import pdf_tool, read_pdf_tool, docx_tool, pptx_tool
from tools.rag import rag_search

# Ensures orchestrator activity is visible in the terminal even if this
# module is imported/run before main.py's own logging.basicConfig has run
# (e.g. standalone scripts, tests). No-ops if the root logger already has
# handlers configured (main.py's own setup takes precedence in that case).
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] [%(name)s] %(message)s",
)
logger = logging.getLogger("agni.brain")
logger.setLevel(logging.INFO)

OLLAMA_TAGS_URL = "http://localhost:11434/api/tags"

# ---- Dynamic Orchestrator Model Resolution ----
def get_best_orchestrator_model() -> str:
    preferred = os.getenv("AGNI_ORCHESTRATOR_MODEL", "qwen2.5:7b-instruct")
    try:
        resp = httpx.get(OLLAMA_TAGS_URL, timeout=2.0)
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
DEFAULT_VISION_MODEL = os.getenv("AGNI_VISION_MODEL", "qwen2.5vl:7b")
logger.info("Brain orchestrator default model: %s", ORCHESTRATOR_MODEL)


def resolve_installed_model(requested: Optional[str]) -> str:
    """Map a model name coming from the frontend's model-card selection
    (payload.model, e.g. 'qwen2.5-coder:7b') to an actually-installed local
    Ollama model. Falls back to a substring match, then the first installed
    model, then the requested/default name unchanged if Ollama can't be
    reached at all."""
    requested = requested or ORCHESTRATOR_MODEL
    try:
        resp = httpx.get(OLLAMA_TAGS_URL, timeout=2.0)
        if resp.status_code == 200:
            installed = [m.get("name") for m in resp.json().get("models", [])]
            if not installed:
                return requested
            if requested in installed:
                return requested
            base = requested.split(":")[0]
            for name in installed:
                if base and base in name:
                    return name
            return installed[0]
    except Exception as e:
        logger.debug("Ollama model check failed while resolving '%s': %s", requested, e)
    return requested


def _looks_vision_capable(model_name: str) -> bool:
    name = (model_name or "").lower()
    return any(tag in name for tag in ("vl", "vision", "llava"))


# ---- Direct tools: the orchestrator (whichever model is selected) calls
# these itself, no separate delegation/rerouter step ----
@tool
def read_file(path: str) -> str:
    """Read the contents of a local file."""
    try:
        resolved = _resolve_attachment_path(path)
        with open(resolved, "r", encoding="utf-8") as f:
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


@tool
def execute_code_tool(code: str) -> str:
    """Execute Python code in an isolated local sandbox (15 second timeout;
    numpy, scipy, matplotlib, pandas available) and return its stdout or
    error output. Use this for calculations, data processing, or generating
    charts/files programmatically. Write complete, runnable code (including
    imports) — this executes exactly what you provide, there is no separate
    coding model involved."""
    from tools.code.code import execute_code

    result = execute_code(code)
    if result.get("status") == "success":
        return f"[Execution succeeded]\n{result.get('output', '')}"
    return f"[Execution failed]\n{result.get('output', '')}"


# Per-thread record of which Ollama model the current request selected (so
# analyze_image can use that exact model when it's vision-capable instead
# of a hardcoded one) and which files are actually attached this turn (so a
# slightly-mistyped path argument can still be resolved). Both are set at
# the top of chatbot_node each turn. threading.local is safe here because
# each brain_graph.invoke() call (one per chat turn) runs synchronously
# start-to-finish on a single worker thread (main.py calls it via
# asyncio.to_thread).
_thread_local = threading.local()

_vision_backend_cache: dict = {}


def _resolve_attachment_path(candidate: str) -> str:
    """Best-effort recovery for a file path argument the model didn't
    transcribe exactly from the [ATTACHED FILES] block in the prompt — a
    local model will sometimes give just the filename, drop/mangle the
    directory, or echo back the attachment's id instead of its full path.
    Matches the candidate against this turn's actual attachments (by exact
    path, id, or filename) and returns the real path if found; otherwise
    returns the candidate unchanged so the caller's own file-not-found
    error still surfaces clearly."""
    if not candidate or os.path.isfile(candidate):
        return candidate

    attachments = getattr(_thread_local, "attachments", None) or []
    candidate_name = os.path.basename(candidate).strip().lower()
    for a in attachments:
        path = a.get("path") or ""
        if not path:
            continue
        if candidate == a.get("id"):
            return path
        name = os.path.basename(path).lower()
        if name == candidate_name:
            return path
    for a in attachments:
        path = a.get("path") or ""
        if path and candidate_name and candidate_name in os.path.basename(path).lower():
            return path
    return candidate


def _get_vision_backend(model_name: str):
    from tools.Vision.vision_module.backend import OllamaVisionBackend

    if model_name not in _vision_backend_cache:
        _vision_backend_cache[model_name] = OllamaVisionBackend(model_name=model_name)
    return _vision_backend_cache[model_name]


_LATEX_CLEANUP_PATTERNS = [
    (re.compile(r"\\\((.*?)\\\)", re.DOTALL), r"\1"),      # \( ... \)  ->  ...
    (re.compile(r"\\\[(.*?)\\\]", re.DOTALL), r"\1"),      # \[ ... \]  ->  ...
    (re.compile(r"\$\$(.*?)\$\$", re.DOTALL), r"\1"),      # $$ ... $$  ->  ...
    (re.compile(r"\$(.*?)\$"), r"\1"),                     # $ ... $    ->  ...
    (re.compile(r"\\text\{([^}]*)\}"), r"\1"),
    (re.compile(r"\\mathrm\{([^}]*)\}"), r"\1"),
    (re.compile(r"\\rightarrow"), "->"),
    (re.compile(r"\\Rightarrow"), "=>"),
    (re.compile(r"\\leftarrow"), "<-"),
    (re.compile(r"\\to\b"), "->"),
    (re.compile(r"\\times"), "x"),
    (re.compile(r"\\cdot"), "*"),
    (re.compile(r"\\neq"), "!="),
    (re.compile(r"\\leq"), "<="),
    (re.compile(r"\\geq"), ">="),
    (re.compile(r"\\infty"), "infinity"),
]


def _strip_latex(text: str) -> str:
    """Safety-net cleanup for stray LaTeX a vision/chat model emits despite
    being told not to. The frontend chat renderer has no math/LaTeX support
    (plain markdown only), so \\( E \\rightarrow E' \\) would otherwise show
    up to the user as literal backslashes and parens instead of "E -> E'"."""
    if not isinstance(text, str) or not text:
        return text
    cleaned = text
    for pattern, repl in _LATEX_CLEANUP_PATTERNS:
        cleaned = pattern.sub(repl, cleaned)
    # Any remaining backslash-escaped command we didn't special-case (e.g.
    # \alpha, \beta) — just drop the backslash so the word stays readable.
    cleaned = re.sub(r"\\([A-Za-z]+)", r"\1", cleaned)
    return cleaned


def _resolve_vision_model(preferred: str) -> Optional[str]:
    """Map a preferred vision model name to one actually installed in
    Ollama — analogous to resolve_installed_model, but specifically prefers
    an installed model that looks vision-capable over just "first
    installed", since a text-only model can't do image analysis at all.
    Returns None if Ollama can't be reached or nothing is installed (the
    caller should surface a clear error rather than call with a guess)."""
    try:
        resp = httpx.get(OLLAMA_TAGS_URL, timeout=2.0)
        if resp.status_code != 200:
            return None
        installed = [m.get("name") for m in resp.json().get("models", [])]
        if not installed:
            return None
        if preferred in installed:
            return preferred
        base = (preferred or "").split(":")[0]
        for name in installed:
            if base and base in name:
                return name
        vision_installed = [m for m in installed if _looks_vision_capable(m)]
        if vision_installed:
            return vision_installed[0]
        return None
    except Exception as e:
        logger.debug("Ollama model check failed while resolving vision model '%s': %s", preferred, e)
        return None


@tool
def analyze_image(image_path: str, query: str = "Describe what you see.") -> str:
    """Analyze a local image file (photo, scanned document, engineering
    diagram, screenshot, handwriting) already available on disk — e.g. a
    path given to you in an [ATTACHED FILES] block. Pass the exact local
    path. Uses the currently selected vision-capable model if one is
    active, otherwise a default local vision model. Do not use this for
    text you can already read directly from a machine-readable file."""
    from tools.Vision.vision_module.schemas import ImageRef

    selected = getattr(_thread_local, "selected_model", None)
    preferred_vision = selected if _looks_vision_capable(selected) else DEFAULT_VISION_MODEL
    resolved_path = _resolve_attachment_path(image_path)
    if resolved_path != image_path:
        logger.info("[TOOL] analyze_image: resolved '%s' -> '%s'", image_path, resolved_path)
    if not os.path.isfile(resolved_path):
        logger.warning("[TOOL] analyze_image: no such file '%s' (from argument '%s')", resolved_path, image_path)
        return (
            f"[Error: no file found at '{image_path}'. Known attachments this turn: "
            f"{[os.path.basename(a.get('path', '')) for a in (getattr(_thread_local, 'attachments', None) or [])]}]"
        )

    vision_model = _resolve_vision_model(preferred_vision)
    if vision_model is None:
        logger.warning(
            "[TOOL] analyze_image: no vision-capable model installed in Ollama (wanted '%s').",
            preferred_vision,
        )
        return (
            "[Error: no vision-capable model is installed in Ollama, or Ollama is "
            f"unreachable. Wanted '{preferred_vision}'. Run `ollama pull qwen2.5vl:3b` "
            "(or another vision model) and try again — this is not a problem with the "
            "image file itself.]"
        )
    if vision_model != preferred_vision:
        logger.info("[TOOL] analyze_image: using installed model '%s' instead of '%s'.", vision_model, preferred_vision)

    try:
        backend = _get_vision_backend(vision_model)
        img = ImageRef(image_id="adhoc", path=resolved_path, timestamp=time.time())
        return _strip_latex(backend.analyze(query, [img]))
    except Exception as e:
        return f"[Error analyzing image {resolved_path}: {e}]"


tools = [
    read_file,
    write_file,
    rag_search,
    pdf_tool,
    read_pdf_tool,
    docx_tool,
    pptx_tool,
    execute_code_tool,
    analyze_image,
]
tool_node = ToolNode(tools)

# ---- Plan -> Review -> Approval -> Implementation workflow ----
# Tools that actually change local state or run code. Anything NOT in this
# set (read_file, rag_search, read_pdf_tool, analyze_image) is treated as
# analysis/read-only and may be called freely at any time, including while
# still building a plan.
WRITE_TOOL_NAMES = {"write_file", "pdf_tool", "docx_tool", "pptx_tool", "execute_code_tool"}

# Sentinel the orchestrator appends (on its own line) to a message that is
# presenting a plan and waiting on the user's approval before it may execute
# anything impactful. Stripped out of the visible text before it's returned
# to the user or persisted — it only exists to flip graph state.
PLAN_SENTINEL = "<<AGNI_PLAN_AWAITING_APPROVAL>>"

APPROVE_RE = re.compile(
    r"\b(yes|yeah|yep|yup|sure|approved?|go\s*ahead|proceed|do\s*it|confirm(?:ed)?|"
    r"sounds?\s*good|looks?\s*good|lgtm|okay|ok)\b",
    re.IGNORECASE,
)
REJECT_RE = re.compile(
    r"\b(no|don'?t|do\s*not|stop|wait|hold\s*on|instead|modify|change\s+(?:that|this|it)|"
    r"actually|not\s+yet)\b",
    re.IGNORECASE,
)


class OrchestratorState(MessagesState):
    """MessagesState plus the plan/approval bookkeeping for one conversation.

    awaiting_approval: the orchestrator just presented a plan and is waiting
        on the user's next message to approve, reject, or request changes.
    approved: the user has approved the plan currently being implemented —
        write tools are allowed through the gate while this is True. It is
        set back to False the moment the orchestrator produces its next
        plain-text reply (a fresh plan or a completion report), so approval
        is single-use per plan, not permanent.
    """
    awaiting_approval: bool
    approved: bool


def _is_write_tool_call(message) -> bool:
    calls = getattr(message, "tool_calls", None) or []
    return any(c.get("name") in WRITE_TOOL_NAMES for c in calls)


def _with_content(message: AIMessage, new_content: str) -> AIMessage:
    """Return a copy of an AIMessage with its content replaced, compatible
    with both pydantic v1 and v2 BaseMessage implementations across
    langchain_core versions."""
    try:
        return message.model_copy(update={"content": new_content})
    except AttributeError:
        return message.copy(update={"content": new_content})


def _system_note_message(content: str) -> HumanMessage:
    """
    Wrap an internal/system note as a HumanMessage rather than an AIMessage.
    Several nodes below (blocked_node) feed their output straight back into
    chatbot_node, which immediately calls the LLM again. If the note were
    appended as another AIMessage, the message history would end in two
    consecutive assistant turns with no human turn between them — most chat
    templates (including Ollama's) treat that as the assistant having
    already replied, and frequently answer with an empty completion.
    Framing it as a (clearly labeled, non-user) human-role turn keeps the
    conversation alternating properly so the model actually generates a
    real text reply.
    """
    return HumanMessage(content=f"[SYSTEM: internal note below — not from the user]\n\n{content}")


# ---- Per-request model selection ----
# The frontend's Model Orchestrator panel picks one model card (General
# Assistant / Engineering Intelligence / Document Vision Analyst); that
# choice now drives the ENTIRE turn — no more LLM-emitted delegation JSON
# and no separate rerouter step picking a different specialist model behind
# the scenes. main.py passes the selected backend model name through
# config={"configurable": {"selected_model": ...}} on each graph.invoke().
_llm_cache: dict = {}


def _get_llm_with_tools(model_name: str):
    if model_name not in _llm_cache:
        logger.info("[ORCHESTRATOR] Initializing ChatOllama for model '%s'.", model_name)
        _llm_cache[model_name] = ChatOllama(model=model_name).bind_tools(tools)
    return _llm_cache[model_name]


def approval_intake_node(state: OrchestratorState, config: dict = None):
    """Runs before the chatbot on every turn. If a plan is pending approval,
    classify the user's latest message as approve / reject-or-modify so the
    gate below knows whether to let implementation through this turn.
    Ambiguous replies are treated as not-yet-approved — the orchestrator
    prompt tells the model to ask for clarification or re-plan in that case,
    rather than silently guessing consent."""
    if not state.get("awaiting_approval"):
        return {}

    messages = state["messages"]
    if not messages:
        return {}
    last = messages[-1]
    if not (isinstance(last, HumanMessage) or getattr(last, "type", None) == "human"):
        return {}

    text = last.content if isinstance(last.content, str) else ""
    approves = bool(APPROVE_RE.search(text))
    rejects = bool(REJECT_RE.search(text))

    if approves and not rejects:
        logger.info("[APPROVAL] User approved the pending plan: %r", text[:160])
        return {"approved": True, "awaiting_approval": False}

    logger.info(
        "[APPROVAL] Pending plan NOT approved (rejected/modified/ambiguous) — will re-plan. reply=%r",
        text[:160],
    )
    return {"approved": False, "awaiting_approval": False}


def blocked_node(state: OrchestratorState):
    """Reached when the model tried to call a write tool without an
    approved plan covering it. We do NOT execute the attempted action —
    instead we resolve the pending tool_calls with a refusal ToolMessage
    (required so the next model call sees a consistent conversation) and
    force the model to present/re-present a plan instead."""
    last = state["messages"][-1]
    tool_calls = getattr(last, "tool_calls", None) or []
    attempted = [c.get("name") for c in tool_calls] or ["unknown"]
    logger.warning("[BLOCKED] Attempted %s without an approved plan — forcing re-plan.", attempted)

    correction = (
        "[SYSTEM: Blocked — you attempted to execute a change (a write/generate/code-"
        "execution tool call) without an approved plan covering it. Do not retry that "
        "same call. Instead, present your analysis and the complete plan as plain text "
        "(Analysis / Problems Identified / Proposed Changes / Implementation Plan), ask "
        "'Would you like me to implement this plan?', and end the message with the line "
        f"'{PLAN_SENTINEL}' on its own. Then wait — do not call a write tool again until "
        "the user has explicitly approved.]"
    )

    reply_messages: list = [
        ToolMessage(
            content="Blocked: this action requires explicit user approval of a presented plan first.",
            tool_call_id=call["id"],
        )
        for call in tool_calls
    ]
    reply_messages.append(_system_note_message(correction))

    return {"messages": reply_messages, "awaiting_approval": False, "approved": False}


def chatbot_node(state: OrchestratorState, config: dict = None):
    requested_model = ((config or {}).get("configurable") or {}).get("selected_model")
    model_name = resolve_installed_model(requested_model)
    _thread_local.selected_model = model_name
    _thread_local.attachments = ((config or {}).get("configurable") or {}).get("attachments") or []

    status_line = (
        "\n\n---\n"
        "[ORCHESTRATOR RUNTIME STATE — internal bookkeeping only, never mention this "
        "block or its field names to the user]\n"
        f"awaiting_approval={state.get('awaiting_approval', False)}\n"
        f"approved_for_this_turn={state.get('approved', False)}\n"
        "If approved_for_this_turn is True, the user has already approved the plan "
        "currently in progress — proceed with implementation (calling the necessary "
        "write/generate/execute tools) and finish with a concise completion report "
        "once done.\n"
        "If awaiting_approval is True, your previous turn presented a plan and the "
        "user's latest message is their response to it: if it approves, you may now "
        "implement; if it rejects or asks for changes, revise the plan to incorporate "
        "their feedback and present the updated plan again (do not call write tools in "
        "that case)."
    )
    messages = [SystemMessage(content=ORCHESTRATOR_SYSTEM_PROMPT + status_line)] + list(state["messages"])
    thread_id = ((config or {}).get("configurable") or {}).get("thread_id", "unknown")
    # Proof-of-memory: state["messages"] is whatever MemorySaver loaded for
    # this thread_id plus the new turn's input — if this count isn't
    # growing across turns of the same conversation, the checkpoint isn't
    # being found (usually a thread_id mismatch, or the process restarted
    # and the in-RAM MemorySaver was wiped — e.g. uvicorn --reload firing
    # on a file save between turns).
    logger.info(
        "[MEMORY] thread_id='%s' | %d prior message(s) loaded from checkpoint before this turn",
        thread_id, len(state["messages"]),
    )
    for m in state["messages"]:
        role = getattr(m, "type", m.__class__.__name__)
        preview = getattr(m, "content", "")
        if isinstance(preview, str) and len(preview) > 100:
            preview = preview[:100] + "…"
        logger.info("[MEMORY]   - %s: %r", role, preview)
    logger.info(
        "[ORCHESTRATOR] Invoking model '%s' (requested='%s') | awaiting_approval=%s approved=%s",
        model_name, requested_model, state.get("awaiting_approval", False), state.get("approved", False),
    )
    llm_with_tools = _get_llm_with_tools(model_name)
    response = llm_with_tools.invoke(messages)

    content = response.content
    awaiting_approval = False
    if isinstance(content, str) and PLAN_SENTINEL in content:
        awaiting_approval = True
        cleaned = re.sub(
            rf"^.*{re.escape(PLAN_SENTINEL)}.*$", "", content, flags=re.MULTILINE
        ).rstrip()
        response = _with_content(response, cleaned)

    has_tool_calls = bool(getattr(response, "tool_calls", None))

    if not has_tool_calls and isinstance(response.content, str):
        # Safety net: strip any stray LaTeX the orchestrator re-quoted from
        # a tool result (e.g. analyze_image output) — the chat UI has no
        # math rendering, so this only ever shows up as literal backslashes.
        response = _with_content(response, _strip_latex(response.content))

    if has_tool_calls:
        names = [c.get("name") for c in response.tool_calls]
        logger.info("[ORCHESTRATOR] Requested tool call(s): %s", names)
    elif awaiting_approval:
        logger.info("[PLAN] Plan presented to user — awaiting approval before any change is made.")
    else:
        logger.info("[ORCHESTRATOR] Final plain-text response returned to user.")

    if has_tool_calls:
        # Mid-flow (an analysis tool call, or an approved write/execute
        # call) — leave awaiting_approval/approved untouched so the gate
        # below and the next loop iteration see accurate state.
        return {"messages": [response]}

    # Plain-text turn: either a freshly presented plan (awaiting_approval
    # True) or a final answer/completion report — either way, any previous
    # approval has now been consumed.
    return {
        "messages": [response],
        "awaiting_approval": awaiting_approval,
        "approved": False,
    }


def route_after_chatbot(state: OrchestratorState):
    last = state["messages"][-1]
    approved = state.get("approved", False)

    if getattr(last, "tool_calls", None):
        if _is_write_tool_call(last) and not approved:
            return "blocked"
        logger.info("[GATE] Routing to tool execution.")
        return "tools"

    logger.info("[GATE] Turn complete — ending.")
    return "end"


def _logged_tool_node(state: OrchestratorState):
    """Thin wrapper around the prebuilt ToolNode that logs which tool is
    about to run (with args) and a preview of what it returned, so tool
    activity shows up in the terminal instead of only the final chat text."""
    last = state["messages"][-1]
    for call in getattr(last, "tool_calls", None) or []:
        logger.info("[TOOL] -> %s(%s)", call.get("name"), call.get("args"))

    result = tool_node.invoke(state)

    for msg in result.get("messages", []):
        content = getattr(msg, "content", "")
        preview = content if not isinstance(content, str) or len(content) <= 200 else content[:200] + "…"
        logger.info("[TOOL] <- %s", preview)

    return result


builder = StateGraph(OrchestratorState)
builder.add_node("approval_intake", approval_intake_node)
builder.add_node("chatbot", chatbot_node)
builder.add_node("tools", _logged_tool_node)
builder.add_node("blocked", blocked_node)

builder.add_edge(START, "approval_intake")
builder.add_edge("approval_intake", "chatbot")
builder.add_conditional_edges(
    "chatbot",
    route_after_chatbot,
    {"tools": "tools", "blocked": "blocked", "end": END}
)
builder.add_edge("tools", "chatbot")
builder.add_edge("blocked", "chatbot")

memory = MemorySaver()
graph = builder.compile(checkpointer=memory)
