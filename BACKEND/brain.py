import ast
import json
import logging
import os
import re
import threading
import time
import uuid
from typing import Optional

import httpx

from langchain_core.messages import AIMessage, HumanMessage, SystemMessage, ToolMessage
from langchain_core.runnables import RunnableConfig
from langchain_core.tools import tool
from langchain_ollama import ChatOllama
from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import END, START, MessagesState, StateGraph
from langgraph.graph.message import add_messages
from langgraph.prebuilt import ToolNode

from prompts.orchestrator_prompt import ORCHESTRATOR_SYSTEM_PROMPT
from tools.pdf import (
    pdf_tool,
    read_pdf_tool,
    read_pptx_tool,
    convert_document_tool,
    docx_tool,
    pptx_tool,
)
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
    Ollama model. Falls back to a substring match, then the general-purpose
    ORCHESTRATOR_MODEL if it's installed (never silently substitute a
    specialized coding/vision model for a general-assistant request just
    because it happened to be first in Ollama's list), then whatever is
    installed, then the requested/default name unchanged if Ollama can't be
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
            # A vision-card request (e.g. "qwen2-vl:7b") whose exact tag
            # isn't installed should prefer whatever vision-capable model IS
            # installed (e.g. "qwen2.5vl:3b") over the generic text-only
            # ORCHESTRATOR_MODEL fallback below — swapping a vision request
            # for a different vision model is a reasonable substitution;
            # swapping it for an unrelated text-only model silently breaks
            # "Document Vision Analyst" into a model that can't see images
            # at all for the whole conversation, not just the analyze_image
            # tool call (which has its own, separate vision-aware fallback).
            if _looks_vision_capable(requested):
                vision_installed = [m for m in installed if _looks_vision_capable(m)]
                if vision_installed:
                    logger.warning(
                        "[MODEL] Requested vision model '%s' is not installed — using "
                        "installed vision model '%s' instead. Run `ollama pull %s` to "
                        "get the exact one configured.",
                        requested, vision_installed[0], requested,
                    )
                    return vision_installed[0]
            if ORCHESTRATOR_MODEL in installed:
                logger.warning(
                    "[MODEL] Requested model '%s' is not installed — falling back to "
                    "general-purpose '%s'. Run `ollama pull %s` to actually use it.",
                    requested, ORCHESTRATOR_MODEL, requested,
                )
                return ORCHESTRATOR_MODEL
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
    read_pptx_tool,
    convert_document_tool,
    docx_tool,
    pptx_tool,
    execute_code_tool,
    analyze_image,
]
tool_node = ToolNode(tools)

# ---- Plan -> Review -> Approval -> Implementation workflow ----
# Destructive/system modifying tools (write_file in workspace, arbitrary code execution)
# require explicit plan approval. Document generation/conversion tools (docx_tool,
# convert_document_tool, pdf_tool, pptx_tool) output standalone deliverables to data/reports/
# and are permitted to execute directly when requested by the user.
WRITE_TOOL_NAMES = {"write_file", "execute_code_tool"}

# Document-generation tools that don't require plan approval (see comment
# above) — meaning `was_approved` never becomes True for these requests at
# all, since no approval step ever happens for them. The stalled/false-
# completion compliance checks below are gated on `was_approved` because
# they'd otherwise misfire on ordinary conversational replies; that gate
# left a real hole for this category specifically: a model asked to "make
# a PPT" can just print the slide content as prose and nothing catches it,
# because none of the was_approved-gated checks ever run for it. Caught
# separately below via GENERATION_INTENT_RE against the user's own request.
DOCGEN_TOOL_NAMES = {"pptx_tool", "docx_tool", "pdf_tool", "convert_document_tool"}

GENERATION_INTENT_RE = re.compile(
    r"\b(make|create|generate|build|produce|draft|prepare|write|export|convert)\b"
    r"[^.\n]{0,40}"
    r"\b(ppt|pptx|powerpoint|presentation|slide\s*deck|slides?|docx|word\s*doc(?:ument)?|"
    r"pdf|deck)\b",
    re.IGNORECASE,
)

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

# Some local models occasionally ignore the "call tools via real
# function-calling, never as text" rule and instead print something that
# looks like {"name": "rag_search", "arguments": {...}} as plain content —
# which executes nothing. Detected and bounced back for a retry rather than
# silently shown to the user as if it were a real answer.
FAKE_TOOLCALL_RE = re.compile(
    r'["\']?(?:name|tool|tool_name|function)["\']?\s*:\s*["\'][^"\']+["\']\s*,\s*["\']?arguments["\']?\s*:',
    re.IGNORECASE,
)

# Some local models, instead of faking JSON, just skip the tool call
# entirely and claim the action already succeeded ("Done. Created a new
# PowerPoint..."). Caught by pairing a completion-claim phrase with the
# absence of any actual write-tool result in recent history.
COMPLETION_CLAIM_RE = re.compile(
    r"\b(done|created|generated|saved|written|updated|completed)\b[^.\n]{0,60}"
    r"\b(successfully|presentation|document|report|file|ppt|pptx|docx|pdf|spreadsheet)\b",
    re.IGNORECASE,
)


def _recent_write_tool_result(messages, lookback: int = 6) -> bool:
    """True if a real write-tool result actually appears in recent history
    (ToolNode-produced ToolMessages carry the tool's name), so we can tell
    a genuine completion report apart from a hallucinated one."""
    for m in list(messages)[-lookback:]:
        if isinstance(m, ToolMessage) and getattr(m, "name", None) in WRITE_TOOL_NAMES:
            return True
    return False


# Generic example-looking paths a model will sometimes echo back (often
# copied from a doc string or this very prompt's own examples) instead of
# the real path a tool actually returned — never a legitimate real path.
PLACEHOLDER_PATH_RE = re.compile(
    r"/(?:abs/path/to|path/to|your/path|your_file|example)\b", re.IGNORECASE
)

# Matches the path out of our own tools' bracketed result strings, e.g.
# "[PowerPoint generated successfully at: /real/path.pptx]" or
# "[Successfully wrote 42 characters to /real/path.txt]".
TOOL_RESULT_PATH_RE = re.compile(r"\b(?:at|to):?\s+([^\s\]]+\.\w+)\]")


def _recent_gen_or_write_tool_result(messages, lookback: int = 6) -> bool:
    """Like _recent_write_tool_result but also counts the no-approval-needed
    document-generation tools (pptx_tool etc.), so a genuine post-generation
    completion report isn't mistaken for a stalled/hallucinated one."""
    names = WRITE_TOOL_NAMES | DOCGEN_TOOL_NAMES
    for m in list(messages)[-lookback:]:
        if isinstance(m, ToolMessage) and getattr(m, "name", None) in names:
            return True
    return False


def _latest_human_text(messages) -> str:
    for m in reversed(list(messages)):
        if isinstance(m, HumanMessage):
            return m.content if isinstance(m.content, str) else ""
    return ""


def _recent_write_tool_paths(messages, lookback: int = 6) -> list:
    """Real file paths pulled from recent write-tool results, most recent
    last, so a correction can hand the model the exact string to use."""
    paths = []
    for m in list(messages)[-lookback:]:
        if isinstance(m, ToolMessage) and getattr(m, "name", None) in WRITE_TOOL_NAMES:
            content = m.content if isinstance(m.content, str) else ""
            match = TOOL_RESULT_PATH_RE.search(content)
            if match:
                paths.append(match.group(1))
    return paths

# ---- Fake-tool-call salvage ----
# Empirically confirmed (live-tested directly against this project's own
# Ollama instance, see conversation history) that some local models —
# specifically qwen2.5-coder:7b, the Engineering Intelligence card's model —
# essentially never populate Ollama's native tool_calls field at all, no
# matter the tool schema (flat or nested) or how explicitly instructed.
# Instead they print a JSON object (or, once told "no JSON", a Python-style
# call or a full code sample) as plain text — often with an invented tool
# name close to but not matching the real one (e.g. "GenerateWordDocument"
# instead of "docx_tool"). Retrying just reproduces byte-identical broken
# output (also verified live), so nagging the model again is futile. Instead
# we parse its stated intent and manually construct the equivalent real tool
# call. That call is then treated exactly like a genuine one — in
# particular, route_after_chatbot still blocks it if it's a write tool and
# nothing has been approved yet — so this can never bypass the plan/approval
# gate; it only ever converts "said it in the wrong format" into "actually
# did it", read-only or write alike.
_REGISTERED_TOOL_NAMES = {t.name for t in tools}

_TOOL_NAME_ALIASES = {
    # Order matters: more specific names (read_pdf_tool) before the more
    # generic ones they'd otherwise be mistaken for (pdf_tool).
    "read_pdf_tool": ("readpdf", "extractpdf", "parsepdf", "ocrpdf"),
    "pptx_tool": ("pptx", "ppt", "powerpoint", "presentation", "slide", "deck"),
    "docx_tool": ("docx", "worddocument", "worddoc", "word"),
    "pdf_tool": ("pdf",),
    "execute_code_tool": ("code", "execute", "python", "sandbox", "runscript"),
    "rag_search": ("rag", "search", "knowledgebase", "retriev"),
    "analyze_image": ("image", "vision", "analyzeimage", "scanimage", "photo"),
    "write_file": ("writefile",),
    "read_file": ("readfile",),
}

_PY_CALL_RE = re.compile(
    r"\b(pptx_tool|docx_tool|pdf_tool|execute_code_tool|rag_search|analyze_image|"
    r"read_pdf_tool|write_file|read_file)\s*\("
)


def _match_tool_name(fake_name: str) -> Optional[str]:
    """Map a hallucinated/approximate tool name (e.g. "GenerateWordDocument")
    to one of our actually-registered tool names, or None if it can't be
    confidently matched to anything."""
    if not fake_name:
        return None
    if fake_name in _REGISTERED_TOOL_NAMES:
        return fake_name
    norm = re.sub(r"[^a-z]", "", fake_name.lower())
    for real_name in _TOOL_NAME_ALIASES:
        if real_name.replace("_", "") == norm:
            return real_name
    for real_name, aliases in _TOOL_NAME_ALIASES.items():
        if not any(alias in norm for alias in aliases):
            continue
        if real_name == "pdf_tool" and "read" in norm:
            continue  # "readpdf..." belongs to read_pdf_tool, not pdf_tool
        if real_name == "write_file" and any(
            k in norm for k in ("pdf", "docx", "pptx", "word", "powerpoint", "ppt", "slide")
        ):
            continue  # a generic "write ... file" mention about a real doc type
        return real_name
    return None


def _normalize_tool_args(tool_name: str, args: dict) -> dict:
    """Light alias handling for argument keys a model invents instead of the
    exact schema (e.g. "text" instead of "content", "heading" instead of
    "title") — best-effort; an unmatched required key is simply left out so
    the tool's own validation/error path handles it cleanly."""
    if not isinstance(args, dict):
        return {}
    args = dict(args)

    def pick(*keys):
        for k in keys:
            if k in args and args[k] not in (None, ""):
                return args.pop(k)
        return None

    if tool_name in ("docx_tool", "pdf_tool"):
        out = {}
        title = pick("title", "heading", "subject", "name")
        content = pick("content", "text", "body")
        if title is not None:
            out["title"] = str(title)
        if content is not None:
            out["content"] = content if isinstance(content, str) else "\n".join(str(c) for c in content) if isinstance(content, list) else str(content)
        filename = pick("filename", "file_name")
        if filename:
            out["filename"] = str(filename)
        return out

    if tool_name == "pptx_tool":
        out = {}
        title = pick("title", "heading", "subject", "name")
        if title is not None:
            out["title"] = str(title)
        slides = pick("slides", "slide_data", "slides_data")
        norm_slides = []
        if isinstance(slides, list):
            for s in slides:
                if isinstance(s, dict):
                    s_title = s.get("title") or s.get("heading") or ""
                    s_content = s.get("content") or s.get("text") or s.get("body")
                    bullets = s.get("bullets") or s.get("points")
                    if s_content is None and isinstance(bullets, list):
                        s_content = "\n".join(str(b) for b in bullets)
                    elif isinstance(s_content, list):
                        s_content = "\n".join(str(c) for c in s_content)
                    norm_slides.append({"title": str(s_title), "content": str(s_content or "")})
                elif isinstance(s, str):
                    norm_slides.append({"title": s, "content": ""})
        out["slides"] = norm_slides
        filename = pick("filename", "file_name")
        if filename:
            out["filename"] = str(filename)
        return out

    if tool_name == "execute_code_tool":
        code = pick("code", "script", "python_code", "source")
        return {"code": code or ""}

    if tool_name == "rag_search":
        query = pick("query", "q", "search_query", "question")
        return {"query": query or ""}

    if tool_name == "read_pdf_tool":
        path = pick("path", "file_path", "filepath", "pdf_path", "filename")
        return {"path": path} if path else {}

    if tool_name == "write_file":
        out = {}
        path = pick("path", "file_path", "filepath", "filename")
        content = pick("content", "text", "body")
        if path:
            out["path"] = path
        if content is not None:
            out["content"] = content if isinstance(content, str) else str(content)
        return out

    if tool_name == "read_file":
        path = pick("path", "file_path", "filepath", "filename")
        return {"path": path} if path else {}

    if tool_name == "analyze_image":
        out = {}
        path = pick("image_path", "path", "file_path")
        query = pick("query", "question", "prompt")
        if path:
            out["image_path"] = path
        if query:
            out["query"] = query
        return out

    return args


def _extract_python_style_call(text: str) -> Optional[tuple]:
    """Detect a Python-style call to one of our real tool names embedded in
    prose/code the model printed instead of using real function-calling,
    e.g. `pptx_tool(title="Tigers", slides=[...])` inside a ```python code
    block. Parses arguments with ast.literal_eval only (never eval/exec),
    so this can extract literal strings/numbers/lists/dicts and nothing
    else — it cannot execute arbitrary code."""
    for match in _PY_CALL_RE.finditer(text):
        name = match.group(1)
        start = match.end() - 1  # index of the opening '('
        depth = 0
        end = None
        for i, ch in enumerate(text[start:], start):
            if ch == "(":
                depth += 1
            elif ch == ")":
                depth -= 1
                if depth == 0:
                    end = i
                    break
        if end is None:
            continue
        inner = text[start + 1:end]
        try:
            call_node = ast.parse(f"f({inner})", mode="eval").body
        except SyntaxError:
            continue
        if not isinstance(call_node, ast.Call) or not call_node.keywords:
            continue
        parsed_args, ok = {}, True
        for kw in call_node.keywords:
            if kw.arg is None:
                ok = False
                break
            try:
                parsed_args[kw.arg] = ast.literal_eval(kw.value)
            except Exception:
                ok = False
                break
        if ok and parsed_args:
            return name, parsed_args
    return None


def _extract_fake_tool_call(raw_text: str) -> Optional[tuple]:
    """Best-effort parse of a model's plain-text fake tool call into
    (real_tool_name, args_dict). Tries a JSON-shaped call first (optionally
    fenced in ```json, or embedded in surrounding prose), then a
    Python-call-syntax form. Returns None if nothing can be confidently
    salvaged, in which case the caller falls back to the existing
    retry-and-correct path."""
    if not raw_text or not raw_text.strip():
        return None
    text = raw_text.strip()

    candidates = []
    fence_match = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", text, re.DOTALL)
    if fence_match:
        candidates.append(fence_match.group(1))
    candidates.append(text)
    start = text.find("{")
    if start != -1:
        depth = 0
        for i, ch in enumerate(text[start:], start):
            if ch == "{":
                depth += 1
            elif ch == "}":
                depth -= 1
                if depth == 0:
                    candidates.append(text[start:i + 1])
                    break

    for candidate in candidates:
        try:
            parsed = json.loads(candidate)
        except Exception:
            continue
        if not isinstance(parsed, dict):
            continue
        fake_name = parsed.get("name") or parsed.get("tool") or parsed.get("tool_name") or parsed.get("function")
        fake_args = parsed.get("arguments")
        if fake_args is None:
            fake_args = parsed.get("args") or parsed.get("parameters")
        if not fake_name or not isinstance(fake_args, dict):
            continue
        real_name = _match_tool_name(str(fake_name))
        if real_name:
            return real_name, _normalize_tool_args(real_name, fake_args)

    py_call = _extract_python_style_call(text)
    if py_call:
        real_name, py_args = py_call
        return real_name, _normalize_tool_args(real_name, py_args)

    return None


def _with_tool_calls(message: AIMessage, tool_calls: list) -> AIMessage:
    """Return a copy of an AIMessage with a real tool_calls list attached and
    content cleared, matching what a genuine tool-calling response looks
    like — used to salvage a model's fake-JSON/Python-text tool call into an
    actual one that flows through the normal approval-gate/execution path."""
    update = {"content": "", "tool_calls": tool_calls}
    try:
        return message.model_copy(update=update)
    except AttributeError:
        return message.copy(update=update)


# Bounded retries, all within a single chatbot_node call (a local loop, not
# extra graph turns) — if the model still won't comply after this many
# corrective nudges, we give up and surface a clear error instead of
# looping forever or leaking broken output to the user.
MAX_COMPLIANCE_RETRIES = 2


class OrchestratorState(MessagesState):
    """MessagesState plus the plan/approval bookkeeping for one conversation.

    awaiting_approval: the orchestrator just presented a plan and is waiting
        on the user's next message to approve, reject, or request changes.
    approved: the user has approved the plan currently being implemented —
        write tools are allowed through the gate while this is True. It is
        set back to False the moment the orchestrator produces its next
        plain-text reply (a fresh plan or a completion report), so approval
        is single-use per plan, not permanent.
    selected_model / attachments / thread_id: per-turn request context.
        Carried in STATE (part of the graph.invoke() input dict) rather
        than config["configurable"], because node functions here were not
        reliably receiving custom configurable keys — thread_id logged as
        'unknown' and selected_model as None on every request even though
        LangGraph's own checkpointer correctly used the invoke-time config
        to load/save state. State fields are proven reliable (message
        history persists correctly), so per-turn context rides along with
        them instead.
    """
    awaiting_approval: bool
    approved: bool
    selected_model: Optional[str]
    attachments: list
    thread_id: Optional[str]


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


NUM_CTX = int(os.getenv("AGNI_NUM_CTX", "16384"))


def _get_llm_with_tools(model_name: str):
    if model_name not in _llm_cache:
        logger.info("[ORCHESTRATOR] Initializing ChatOllama for model '%s' (num_ctx=%d).", model_name, NUM_CTX)
        _llm_cache[model_name] = ChatOllama(
            model=model_name,
            num_ctx=NUM_CTX,
            temperature=0.3,
        ).bind_tools(tools)
    return _llm_cache[model_name]


def approval_intake_node(state: OrchestratorState, config: Optional[RunnableConfig] = None):
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


def chatbot_node(state: OrchestratorState, config: Optional[RunnableConfig] = None):
    requested_model = state.get("selected_model")
    model_name = resolve_installed_model(requested_model)
    _thread_local.selected_model = model_name
    _thread_local.attachments = state.get("attachments") or []

    status_line = (
        "\n\n---\n"
        "[ORCHESTRATOR RUNTIME STATE — internal bookkeeping only, never mention this "
        "block or its field names to the user]\n"
        f"awaiting_approval={state.get('awaiting_approval', False)}\n"
        f"approved_for_this_turn={state.get('approved', False)}\n"
        "If approved_for_this_turn is True, the user has ALREADY approved the plan "
        "currently in progress in an earlier turn — do NOT ask for approval again and "
        "do NOT present another plan. Call the necessary write/generate/execute "
        "tool(s) right now via real function-calling, then finish with a concise "
        "completion report once done.\n"
        "If awaiting_approval is True, your previous turn presented a plan and the "
        "user's latest message is their response to it: if it approves, you may now "
        "implement; if it rejects or asks for changes, revise the plan to incorporate "
        "their feedback and present the updated plan again (do not call write tools in "
        "that case)."
    )
    base_messages = [SystemMessage(content=ORCHESTRATOR_SYSTEM_PROMPT + status_line)] + list(state["messages"])
    thread_id = state.get("thread_id") or ((config or {}).get("configurable") or {}).get("thread_id", "unknown")
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

    was_approved = state.get("approved", False)  # snapshot — our own return below overwrites this key
    logger.info(
        "[ORCHESTRATOR] Invoking model '%s' (requested='%s') | awaiting_approval=%s approved=%s",
        model_name, requested_model, state.get("awaiting_approval", False), was_approved,
    )
    llm_with_tools = _get_llm_with_tools(model_name)

    # Bounded local retry loop (NOT extra graph turns — this all happens
    # inside one chatbot_node call) for two hard rules a small model will
    # occasionally break: (1) call tools via real function-calling, never
    # print one as JSON text, and (2) don't re-ask for approval once the
    # user has already approved this plan in an earlier turn. Both are
    # mechanically detectable, so we bounce the model back with a
    # corrective note and retry rather than showing the user a repeat
    # question or a dead JSON blob that executed nothing.
    extra_messages: list = []
    response = None
    awaiting_approval = False
    has_tool_calls = False
    gave_up_reason = None

    for attempt in range(MAX_COMPLIANCE_RETRIES + 1):
        response = llm_with_tools.invoke(base_messages + extra_messages)

        content = response.content
        awaiting_approval = False
        if isinstance(content, str) and PLAN_SENTINEL in content:
            awaiting_approval = True
            cleaned = re.sub(
                rf"^.*{re.escape(PLAN_SENTINEL)}.*$", "", content, flags=re.MULTILINE
            ).rstrip()
            response = _with_content(response, cleaned)

        has_tool_calls = bool(getattr(response, "tool_calls", None))

        noncompliance = None
        if not has_tool_calls:
            raw_text = response.content if isinstance(response.content, str) else ""

            # Try to salvage a fake-text tool call into a real one before
            # falling back to nagging the model to retry (see the
            # _extract_fake_tool_call docstring/comment above for why: for
            # at least one of this project's installed models, retrying
            # this specific failure mode reproduces byte-identical broken
            # output). Skipped while a plan is being presented this turn —
            # awaiting_approval means the model is asking a question, not
            # trying (badly) to act.
            salvaged = None if awaiting_approval else _extract_fake_tool_call(raw_text)
            if salvaged:
                real_name, real_args = salvaged
                call_id = f"salvaged_{uuid.uuid4().hex[:8]}"
                logger.warning(
                    "[COMPLIANCE] Model '%s' expressed a tool call as plain text "
                    "(%r) instead of real function-calling — salvaging it into a "
                    "real %s(%s) call instead of retrying.",
                    model_name, raw_text[:120], real_name, real_args,
                )
                response = _with_tool_calls(response, [
                    {"name": real_name, "args": real_args, "id": call_id, "type": "tool_call"}
                ])
                has_tool_calls = True
            elif FAKE_TOOLCALL_RE.search(raw_text):
                noncompliance = "fake_json"
            elif awaiting_approval and was_approved:
                noncompliance = "reasked"
            elif PLACEHOLDER_PATH_RE.search(raw_text):
                noncompliance = "placeholder_path"
            elif (
                was_approved
                and COMPLETION_CLAIM_RE.search(raw_text)
                and not _recent_write_tool_result(state["messages"])
            ):
                noncompliance = "false_completion"
            elif (
                was_approved
                and not awaiting_approval
                and "?" not in raw_text.strip()
                and not _recent_write_tool_result(state["messages"])
            ):
                # Approved to implement, didn't call a tool, didn't
                # re-present a plan, didn't ask a genuine clarifying
                # question, and no write tool has actually run yet this
                # session — just stalled with commentary/narration ("Sure,
                # let's proceed...", "Here's the code to run:") instead of
                # actually acting. (A genuine completion report after a
                # real tool result already exists is excluded here, and
                # handled — or rather, accepted — because it fails this
                # last condition.)
                noncompliance = "stalled_without_acting"
            elif (
                not awaiting_approval
                and "?" not in raw_text.strip()
                and GENERATION_INTENT_RE.search(_latest_human_text(state["messages"]))
                and not _recent_gen_or_write_tool_result(state["messages"])
            ):
                # Document-generation tools (pptx_tool/docx_tool/pdf_tool/
                # convert_document_tool) never go through the plan/approval
                # step, so was_approved is never True for them — meaning the
                # was_approved-gated checks above never catch a model that
                # just prints the slide/document content as prose instead of
                # actually calling the tool. Caught here instead, keyed off
                # the user's own request rather than approval state.
                noncompliance = "no_gen_tool_call"

        if noncompliance is None:
            break

        if attempt == MAX_COMPLIANCE_RETRIES:
            gave_up_reason = noncompliance
            break

        logger.warning(
            "[COMPLIANCE] Model non-compliance '%s' (attempt %d/%d) — retrying within this turn.",
            noncompliance, attempt + 1, MAX_COMPLIANCE_RETRIES,
        )
        correction_text = {
            "fake_json": (
                "[SYSTEM: You just wrote what looks like a tool call as plain JSON text "
                "instead of actually invoking it. That executed nothing — no search ran, "
                "no file was touched. Call the tool directly now via the real "
                "function-calling mechanism: no visible JSON, no code block, no "
                "narration.]"
            ),
            "reasked": (
                "[SYSTEM: The user already approved this plan in an earlier turn. Do not "
                "ask for approval again and do not present another plan. Call the "
                "necessary write/generate/execute tool(s) right now to implement it.]"
            ),
            "false_completion": (
                "[SYSTEM: You just claimed an action (creating/generating/saving something) "
                "was completed, but you did not actually call any tool this turn, and there "
                "is no matching tool result in the conversation confirming it. Do not claim "
                "something is done unless you actually called the corresponding tool via "
                "real function-calling and it returned a result. Call the necessary tool "
                "now.]"
            ),
            "placeholder_path": (
                (
                    "[SYSTEM: You reported a placeholder-looking path instead of a real one. "
                    f"The actual path from the tool's result is: {p}. Report that exact string "
                    "to the user, character for character — never a generic example path like "
                    "'/abs/path/to/...'.]"
                ) if (p := (_recent_write_tool_paths(state["messages"]) or [None])[-1])
                else (
                    "[SYSTEM: You reported a placeholder-looking path (like '/abs/path/to/...') "
                    "instead of a real one. Only state a file path that was actually returned "
                    "by a tool result — never invent or copy an example/generic path.]"
                )
            ),
            "stalled_without_acting": (
                "[SYSTEM: The user already approved this — you responded with commentary or "
                "example code instead of actually calling a tool. Writing code, a shell "
                "command, or a plan in your text response does nothing by itself. Call the "
                "necessary tool (e.g. execute_code_tool, pptx_tool, docx_tool) right now via "
                "real function-calling to actually do the work.]"
            ),
            "no_gen_tool_call": (
                "[SYSTEM: The user asked you to generate a file (a presentation, Word "
                "document, or PDF), but you responded with the content as plain text "
                "instead of actually calling the generation tool. Writing the outline or "
                "slide content in your chat reply does nothing by itself — no file is "
                "created. Call the matching tool now via real function-calling (pptx_tool "
                "for a presentation, docx_tool for a Word document, pdf_tool for a PDF) "
                "with that same content, so it is actually saved to disk.]"
            ),
        }[noncompliance]
        extra_messages = extra_messages + [response, _system_note_message(correction_text)]

    if gave_up_reason:
        logger.warning(
            "[COMPLIANCE] Giving up after %d retries (%s) — returning an explicit error instead of broken output.",
            MAX_COMPLIANCE_RETRIES, gave_up_reason,
        )
        response = _with_content(
            response,
            "I wasn't able to complete that action after a few attempts — something in my "
            "own response kept coming out malformed. Could you try rephrasing the request?",
        )
        awaiting_approval = False
        has_tool_calls = False

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
