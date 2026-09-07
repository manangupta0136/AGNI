"""
ollama_client.py

Acts as the rerouter's execution layer: given a delegation JSON from the
orchestrator ({"action": "vision" | "code", "stm": [...]}), this module
decides which specialist model to invoke, ensures the correct models are
loaded/evicted in Ollama, and returns the specialist's response.

Residency rules enforced here:
  - Orchestrator, Vision, and Coding are NEVER all three loaded at once.
  - Orchestrator + at most ONE specialist may be resident simultaneously.
  - If Coding is requested while Vision is loaded (or vice versa), the
    other specialist is force-evicted BEFORE the new one loads.
  - Every model (orchestrator included) uses a 5-minute keep_alive window.
    If nothing calls a given model again within 5 minutes, Ollama evicts
    it on its own — this is what naturally "sleeps" the orchestrator if
    a specialist task runs long, and sleeps a specialist if it goes idle.
"""

import ollama
from typing import Literal

KEEP_ALIVE_WINDOW = "5m"

MODEL_REGISTRY = {
    "orchestrator": "qwen2.5:7b-instruct",
    "vision": "qwen2.5vl:7b",
    "code": "qwen2.5-coder:7b",
}

# Tracks which specialist (vision/code) is currently believed to be
# resident, so we know whether an eviction is needed before loading a
# different one. None means no specialist is currently loaded.
_current_specialist: str | None = None


def _stop_model(model_name: str):
    """
    Force-evicts a model from memory immediately, regardless of its
    keep_alive window. Used when switching between vision and code, so
    we never exceed the "orchestrator + 1 specialist" residency limit.
    """
    try:
        ollama.generate(model=model_name, prompt="", keep_alive=0)
    except Exception as e:
        # Not fatal — if the model wasn't loaded anyway, this is a no-op
        # in practice. Log for visibility during development/demo.
        print(f"[ollama_client] Note: stop_model('{model_name}') — {e}")


def call_orchestrator(messages: list[dict]) -> dict:
    """
    Calls the orchestrator model. Always uses the same 5-minute
    keep_alive window as the specialists — this is intentional, per the
    design: the orchestrator isn't hard-coded as "always loaded", it just
    naturally stays warm because it's called at the start and end of
    almost every turn. If a specialist task runs longer than 5 minutes
    without the orchestrator being touched, it will idle out on its own,
    exactly like a specialist would.
    """
    response = ollama.chat(
        model=MODEL_REGISTRY["orchestrator"],
        messages=messages,
        keep_alive=KEEP_ALIVE_WINDOW,
    )
    return response


def route_to_specialist(action: Literal["vision", "code"], stm: list[dict]) -> dict:
    """
    The rerouter's core function. Takes the orchestrator's delegation
    decision and the short-term memory to forward, ensures correct model
    residency (evicting the other specialist if needed), calls the
    chosen specialist, and returns its response.

    action must be exactly "vision" or "code" — enforced by the type
    hint and validated explicitly below since this value originates from
    a parsed LLM output, not a trusted internal caller.
    """
    global _current_specialist

    if action not in ("vision", "code"):
        raise ValueError(f"Invalid action '{action}' — must be 'vision' or 'code'")

    # If a DIFFERENT specialist is currently loaded, evict it first.
    # This guarantees at most one specialist is ever resident alongside
    # the orchestrator.
    if _current_specialist is not None and _current_specialist != action:
        _stop_model(MODEL_REGISTRY[_current_specialist])

    model_name = MODEL_REGISTRY[action]

    response = ollama.chat(
        model=model_name,
        messages=stm,
        keep_alive=KEEP_ALIVE_WINDOW,
    )

    _current_specialist = action
    return response


def current_status() -> dict:
    """
    Small helper for a /models/status endpoint or demo transparency —
    reports what this module currently believes is loaded. For ground
    truth (not just this module's internal tracking), pair this with
    `ollama.ps()` directly where needed.
    """
    return {
        "orchestrator": MODEL_REGISTRY["orchestrator"],
        "current_specialist": _current_specialist,
        "current_specialist_model": MODEL_REGISTRY.get(_current_specialist) if _current_specialist else None,
    }