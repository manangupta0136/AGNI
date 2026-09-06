"""
FastAPI router for the vision tool.

Two endpoints:
  POST /tools/vision/upload  -> call this whenever the user shares a new image
                                 (drag-drop, screenshot, camera capture). Puts
                                 it in short-term memory, returns an image_id.
  POST /tools/vision/invoke  -> call this from the reroute layer when the
                                 orchestrator's action json says action == "vision".

Wire this into your main app with:
    from vision_module.router import router as vision_router
    app.include_router(vision_router)
"""

import os
import shutil
import uuid

from fastapi import APIRouter, UploadFile, File, Form

from .schemas import VisionRequest, VisionResult
from .memory_store import ShortTermImageMemory
from .backend import Qwen25VLBackend
from .tool import VisionTool

router = APIRouter(prefix="/tools/vision", tags=["vision"])

# --- wiring -----------------------------------------------------------
# Requires: `ollama pull qwen2.5vl:7b` once (needs internet that one time),
# then `ollama serve` running locally -- everything after that is offline.
# For a lighter/faster demo machine, use qwen2.5vl:3b instead.
memory = ShortTermImageMemory(ttl_seconds=1800, max_images_per_session=20)
backend = Qwen25VLBackend(model_name="qwen2.5vl:3b")
tool = VisionTool(memory=memory, backend=backend)

UPLOAD_DIR = "vision_uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)
# ------------------------------------------------------------------------


@router.post("/upload")
async def upload_image(
    session_id: str = Form(...),
    file: UploadFile = File(...),
    auto_scan: bool = Form(True),
):
    """Handles a newly uploaded image. With auto_scan=True (the default), the
    image is analyzed immediately with Qwen2.5-VL and the result is returned
    right away, matching "user uploads -> we scan and analyze" -- no extra
    round trip through the orchestrator needed for the base case. Set
    auto_scan=False if you'd rather wait and let a specific user query
    (via /invoke) drive what gets analyzed."""
    ext = os.path.splitext(file.filename or "")[1]
    save_path = os.path.join(UPLOAD_DIR, f"{uuid.uuid4().hex}{ext}")
    with open(save_path, "wb") as f:
        shutil.copyfileobj(file.file, f)

    images = tool.register_new_images(session_id, [save_path], source="upload")

    if not auto_scan:
        return {"status": "ok", "image_ids": [img.image_id for img in images]}

    scan_result = tool.scan_uploaded_images(session_id, images)
    return {"status": "ok", "image_ids": [img.image_id for img in images], "scan": scan_result}


@router.post("/invoke", response_model=VisionResult)
async def invoke_vision(request: VisionRequest):
    return tool.handle(request)
