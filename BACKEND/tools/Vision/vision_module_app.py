"""
Standalone runner: lets you test the vision module by itself before wiring it
into your real orchestrator/reroute layer.

Run with:  uvicorn vision_module_app:app --reload
Then visit http://127.0.0.1:8000/docs to try the endpoints interactively.
"""

from fastapi import FastAPI
from vision_module.router import router as vision_router

app = FastAPI(title="Vision Tool - standalone test app")
app.include_router(vision_router)


@app.get("/")
def root():
    return {"status": "vision module running"}
