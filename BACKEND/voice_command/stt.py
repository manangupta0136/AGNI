"""
stt.py
Speech-to-text using faster-whisper. Loaded once at import time and kept
resident — this model is small enough (~500MB for 'small') that it doesn't
need swap/eviction logic like the LLMs do.
"""

from faster_whisper import WhisperModel

MODEL_SIZE = "small"   # tiny / base / small / medium — small is a good accuracy/speed balance

# compute_type="int8" keeps RAM/CPU usage low with minimal accuracy loss —
# a sensible default on a memory-constrained laptop
model = WhisperModel(MODEL_SIZE, device="cpu", compute_type="int8")


def transcribe_audio(filepath: str) -> str:
    """
    Takes a path to an audio file (wav/mp3/webm/etc — faster-whisper handles
    most common formats via ffmpeg under the hood) and returns the
    transcribed text as a single string.
    """
    segments, _info = model.transcribe(filepath, beam_size=5)
    text = " ".join(segment.text.strip() for segment in segments)
    return text.strip()