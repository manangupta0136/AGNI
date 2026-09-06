"""
Shared JSON contract for the vision tool.

This matches the pipeline you designed:
orchestrator -> reroute layer -> vision tool -> reroute layer -> orchestrator

The orchestrator and reroute layer only ever pass IDs and small metadata around,
never raw image bytes or full documents. Full image bytes live on disk (or an
object store later) and are looked up by image_id inside this module.
"""

from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field


class ImageRef(BaseModel):
    """One image currently held in the vision tool's short-term memory."""
    image_id: str
    path: str
    caption: Optional[str] = None
    source: str = "upload"  # "upload" | "screenshot" | "camera"
    timestamp: float


class STM(BaseModel):
    """Short-term memory snapshot as passed down from the orchestrator.

    recent_turns is the chat history slice relevant to this call.
    active_images is optional -- if the orchestrator already knows which
    images are "in play" it can pass them; otherwise the vision tool falls
    back to its own memory store keyed by session_id.
    """
    recent_turns: List[Dict[str, Any]] = Field(default_factory=list)
    active_images: List[str] = Field(default_factory=list)  # image_ids


class VisionRequest(BaseModel):
    """What the reroute layer sends to the vision tool."""
    session_id: str
    action: str = "vision"
    payload: Dict[str, Any]  # expects {"query": str, "image_refs": Optional[List[str]]}
    stm: STM = Field(default_factory=STM)
    ltm_refs: List[str] = Field(default_factory=list)  # pointers into long-term memory / vector DB


class VisionResult(BaseModel):
    """What the vision tool hands back to the reroute layer, which forwards it
    to the orchestrator to merge into memory and the db."""
    session_id: str
    action: str = "vision_result"
    result: Dict[str, Any]
    stm_update: Dict[str, Any]
