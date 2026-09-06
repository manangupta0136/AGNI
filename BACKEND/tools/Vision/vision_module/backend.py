"""
The actual multimodal model call, kept behind an interface so you can swap
models without touching the rest of the pipeline.

For "sovereign on-prem" you'll most likely run an open-weight vision model
(Qwen2-VL, LLaVA-NeXT, Llama 3.2 Vision, InternVL2, etc.) locally via Ollama
or vLLM. OllamaVisionBackend below assumes Ollama running on localhost --
swap base_url/model_name for your actual setup, or write a new backend class
with the same .analyze() signature if you use vLLM's OpenAI-compatible API
instead.
"""

import base64
from typing import List

import requests

from .schemas import ImageRef


DEFAULT_SCAN_PROMPT = (
    "Carefully scan this image and analyze it. Describe what it shows, "
    "extract any visible text verbatim, list any tables/forms/diagrams "
    "present, and flag anything that looks like a defect, anomaly, or "
    "safety issue if this is an industrial/technical image. Be specific "
    "and structured in your answer."
)


class VisionModelBackend:
    def analyze(self, query: str, images: List[ImageRef]) -> str:
        raise NotImplementedError

    def scan(self, images: List[ImageRef]) -> str:
        """Called for auto-analysis right when an image is uploaded, before
        the user has asked anything specific. Default: run analyze() with a
        generic scan prompt; subclasses can override with a tuned prompt."""
        return self.analyze(DEFAULT_SCAN_PROMPT, images)


class OllamaVisionBackend(VisionModelBackend):
    def __init__(self, model_name: str = "llava", base_url: str = "http://localhost:11434"):
        self.model_name = model_name
        self.base_url = base_url.rstrip("/")

    def analyze(self, query: str, images: List[ImageRef]) -> str:
        image_b64_list = []
        for img in images:
            with open(img.path, "rb") as f:
                image_b64_list.append(base64.b64encode(f.read()).decode("utf-8"))

        response = requests.post(
            f"{self.base_url}/api/generate",
            json={
                "model": self.model_name,
                "prompt": query,
                "images": image_b64_list,
                "stream": False,
            },
            timeout=600,
        )
        response.raise_for_status()
        return response.json().get("response", "")


class Qwen25VLBackend(OllamaVisionBackend):
    """Qwen2.5-VL running locally via Ollama -- fully offline at inference time.

    One-time setup (needs internet once, to pull the model):
        ollama pull qwen2.5vl:7b        # good balance of quality/speed, ~6GB
        # or qwen2.5vl:3b  (~3.2GB, lighter/faster, weaker on dense docs)
        # or qwen2.5vl:32b (~21GB, needs a real GPU, much stronger on
        #                   scanned documents / small text / diagrams)

    After that, `ollama serve` runs entirely on-device with no network calls,
    which is what you need for the "sovereign on-prem" requirement in 26117.
    """

    def __init__(self, model_name: str = "qwen2.5vl:7b", base_url: str = "http://localhost:11434"):
        super().__init__(model_name=model_name, base_url=base_url)


class StubVisionBackend(VisionModelBackend):
    """Returns a fake answer so you can test the full pipeline (upload -> memory
    -> orchestrator -> reroute -> vision -> back) before the real model is wired up."""

    def analyze(self, query: str, images: List[ImageRef]) -> str:
        names = ", ".join(img.image_id for img in images) or "no images"
        return f"[stub response] would analyze [{names}] for query: '{query}'"
