"""
The vision tool itself: what the reroute layer actually calls.

handle() is the single entrypoint matching the contract you designed --
it takes a VisionRequest and always returns a VisionResult, so the reroute
layer never needs to know anything about images, models, or memory internals.
"""

import time
import uuid
from typing import List

from .schemas import VisionRequest, VisionResult, ImageRef
from .memory_store import ShortTermImageMemory
from .backend import VisionModelBackend


class VisionTool:
    def __init__(self, memory: ShortTermImageMemory, backend: VisionModelBackend):
        self.memory = memory
        self.backend = backend

    def register_new_images(self, session_id: str, image_paths: List[str], source: str = "upload") -> List[ImageRef]:
        """Call this the moment a new image lands (upload endpoint, screenshot capture,
        etc), separately from invoking the model. This is what makes the image
        available in short-term memory for the vision tool to use later."""
        new_images = []
        for path in image_paths:
            img = ImageRef(
                image_id=uuid.uuid4().hex[:8],
                path=path,
                source=source,
                timestamp=time.time(),
            )
            self.memory.add_image(session_id, img)
            new_images.append(img)
        return new_images

    def scan_uploaded_images(self, session_id: str, images: List[ImageRef]) -> VisionResult:
        """Runs immediately on upload, before the user has typed anything --
        this is the 'scan and analyze on upload' behavior. Each image gets
        analyzed on its own so a bad/slow image doesn't block the others, and
        the caption is stashed back onto the ImageRef in memory so a later
        query can reference "that image" without re-running the full model."""
        results = []
        for img in images:
            caption = self.backend.scan([img])
            img.caption = caption
            results.append({"image_id": img.image_id, "analysis": caption})

        return VisionResult(
            session_id=session_id,
            action="vision_scan_result",
            result={"scanned": results},
            stm_update={"active_images": [img.image_id for img in images]},
        )

    def handle(self, request: VisionRequest) -> VisionResult:
        requested_ids = request.payload.get("image_refs") or None
        images = self.memory.get_images(request.session_id, requested_ids)

        if not images:
            return VisionResult(
                session_id=request.session_id,
                result={
                    "text": "No images available in short-term memory for this session.",
                    "error": "no_images",
                },
                stm_update={"active_images": []},
            )

        query = request.payload.get("query", "Describe what you see.")
        answer = self.backend.analyze(query, images)

        return VisionResult(
            session_id=request.session_id,
            result={
                "text": answer,
                "image_ids_used": [img.image_id for img in images],
            },
            stm_update={"active_images": [img.image_id for img in images]},
        )
