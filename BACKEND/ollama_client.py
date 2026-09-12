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

from __future__ import annotations

import logging
import os
from typing import Literal

import ollama

logger = logging.getLogger("agni.ollama_client")

KEEP_ALIVE_WINDOW = "5m"

MODEL_REGISTRY = {
    "orchestrator": os.getenv("AGNI_ORCHESTRATOR_MODEL", "qwen2.5:7b-instruct"),
    "vision": os.getenv("AGNI_VISION_MODEL", "qwen2.5vl:7b"),
    "code": os.getenv("AGNI_CODE_MODEL", "qwen2.5-coder:7b"),
}

# Tracks which specialist (vision/code) is currently believed to be
# resident, so we know whether an eviction is needed before loading a
# different one. None means no specialist is currently loaded.
_current_specialist: str | None = None


def resolve_model(role: Literal["vision", "code", "orchestrator"]) -> str:
    """Resolve configured model to an actually installed Ollama model."""
    preferred = MODEL_REGISTRY.get(role, "mistral:latest")
    try:
        models_resp = ollama.list()
        installed = [m.model for m in models_resp.models]
        if preferred in installed:
            return preferred
        
        # Check known fallback candidates
        candidate_map = {
            "code": ["qwen2.5-coder:7b", "deepseek-r1:1.5b", "codellama", "mistral:latest"],
            "vision": ["qwen2.5vl:7b", "qwen2-vl:7b", "llava:latest", "mistral:latest"],
            "orchestrator": ["qwen2.5:7b-instruct", "mistral:latest", "llama3.1:8b", "deepseek-r1:1.5b"],
        }
        for cand in candidate_map.get(role, []):
            for inst in installed:
                if cand in inst:
                    return inst
        if installed:
            return installed[0]
    except Exception as e:
        logger.debug("Failed to list installed Ollama models: %s", e)
    return preferred


def _stop_model(model_name: str):
    """
    Force-evicts a model from memory immediately, regardless of its
    keep_alive window. Used when switching between vision and code, so
    we never exceed the "orchestrator + 1 specialist" residency limit.
    """
    try:
        ollama.generate(model=model_name, prompt="", keep_alive=0)
    except Exception as e:
        print(f"[ollama_client] Note: stop_model('{model_name}') — {e}")


def call_orchestrator(messages: list[dict]) -> dict:
    """Calls the orchestrator model with dynamic resolution."""
    model_name = resolve_model("orchestrator")
    response = ollama.chat(
        model=model_name,
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
    """
    global _current_specialist

    if action not in ("vision", "code"):
        raise ValueError(f"Invalid action '{action}' — must be 'vision' or 'code'")

    model_name = resolve_model(action)

    # If a DIFFERENT specialist is currently loaded, evict it first.
    if _current_specialist is not None and _current_specialist != action:
        old_model = resolve_model(_current_specialist)
        _stop_model(old_model)

    response = ollama.chat(
        model=model_name,
        messages=stm,
        keep_alive=KEEP_ALIVE_WINDOW,
    )

    _current_specialist = action
    return response


def current_status() -> dict:
    """Reports what this module currently believes is loaded."""
    return {
        "orchestrator": resolve_model("orchestrator"),
        "current_specialist": _current_specialist,
        "current_specialist_model": resolve_model(_current_specialist) if _current_specialist else None,
    }