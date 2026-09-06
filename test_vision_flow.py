"""
Sanity test that doesn't need a running server -- exercises the vision tool
directly the way the reroute layer eventually will.

Run with: python test_vision_flow.py
"""

from vision_module.memory_store import ShortTermImageMemory
from vision_module.backend import StubVisionBackend
from vision_module.tool import VisionTool
from vision_module.schemas import VisionRequest

# 1. set up the tool the same way router.py does
# (using the stub here so this test doesn't need Ollama/Qwen2.5-VL running --
# swap in Qwen25VLBackend() to test against the real local model)
memory = ShortTermImageMemory()
backend = StubVisionBackend()
tool = VisionTool(memory=memory, backend=backend)

session_id = "test-session-1"

# 2. simulate an image arriving (this is what /upload does)
# using this script itself as a stand-in file since we just need a real path
registered = tool.register_new_images(session_id, image_paths=[__file__], source="upload")
print("Registered images:", [img.image_id for img in registered])

# 2b. simulate auto-scan-on-upload
scan_result = tool.scan_uploaded_images(session_id, registered)
print("\nAuto-scan result (runs immediately on upload):")
print(scan_result.model_dump_json(indent=2))

# 3. simulate the reroute layer calling /invoke with the orchestrator's action json
request = VisionRequest(
    session_id=session_id,
    action="vision",
    payload={"query": "What is in this image?"},
)
result = tool.handle(request)

print("\nVisionResult returned to reroute layer / orchestrator:")
print(result.model_dump_json(indent=2))
