# Vision Tool Module (SIH 26117)

Self-contained vision tool: action button target for your orchestrator, with
its own short-term image memory, ready to plug into the reroute layer.

## Files
- `vision_module/schemas.py` — the JSON contract (VisionRequest / VisionResult) shared with the orchestrator and reroute layer
- `vision_module/memory_store.py` — short-term memory: which images are "in play" per session
- `vision_module/backend.py` — the actual model call (stub for now, Ollama adapter included)
- `vision_module/tool.py` — ties memory + backend together, the real logic
- `vision_module/router.py` — FastAPI endpoints: `/tools/vision/upload`, `/tools/vision/invoke`
- `vision_module_app.py` — standalone app to test this module by itself
- `test_vision_flow.py` — no-server sanity test

## Run it standalone
```bash
pip install -r requirements.txt
python test_vision_flow.py          # quick check, no server needed
uvicorn vision_module_app:app --reload   # then open http://127.0.0.1:8000/docs
```

## Wire into your real backend
```python
from vision_module.router import router as vision_router
app.include_router(vision_router)
```

Your reroute layer calls `POST /tools/vision/invoke` with a `VisionRequest`
JSON body whenever the orchestrator's action json says `"action": "vision"`,
and gets a `VisionResult` back to hand to the orchestrator.

## Running fully offline with Qwen2.5-VL

`router.py` is already wired to `Qwen25VLBackend`, which calls a local Ollama
server. One-time setup (needs internet just this once, to download the model):

```bash
ollama pull qwen2.5vl:7b      # ~6GB, good balance for a demo laptop
# or qwen2.5vl:3b             # ~3.2GB, lighter/faster, weaker on dense text
# or qwen2.5vl:32b            # ~21GB, needs a real GPU, much stronger on
#                               scanned documents / small text / diagrams
```

Then keep `ollama serve` running in the background. After the model is
pulled, everything runs on-device with zero network calls — that satisfies
the offline / sovereign requirement in 26117.

If Ollama isn't running yet (e.g. testing on a sandbox or CI box), swap back
to `StubVisionBackend()` in `router.py` — same interface, fake responses,
useful for testing the pipeline shape before the model server is up.

## Scan-on-upload

`POST /tools/vision/upload` now runs the model immediately after the image
is saved (`auto_scan=True` by default), so "user uploads an image" directly
triggers "we scan and analyze it" without waiting for a separate query. The
response includes the scan result inline. Set `auto_scan=False` in the form
data if you'd rather defer analysis until the user asks something specific
via `/tools/vision/invoke`.

The scan prompt (`DEFAULT_SCAN_PROMPT` in `backend.py`) asks the model to
describe the image, transcribe visible text, list tables/diagrams, and flag
anything that looks like a defect or safety issue — tune this wording for
your actual use case (pure OCR/document focus vs. industrial defect focus).

## Scaling note
`ShortTermImageMemory` is an in-memory dict, fine for a single-process demo.
Move it to Redis (same method names: add/get/clear) before running multiple
workers or processes, or sessions will land inconsistently across workers.
