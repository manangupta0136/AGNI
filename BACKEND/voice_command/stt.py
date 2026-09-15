"""
stt.py
Speech-to-text using faster-whisper. Loaded once at import time and kept
resident — this model is small enough (~500MB for 'small') that it doesn't
need swap/eviction logic like the LLMs do.
"""

import threading

from faster_whisper import WhisperModel

MODEL_SIZE = "small"   # tiny / base / small / medium — small is a good accuracy/speed balance

# compute_type="int8" keeps RAM/CPU usage low with minimal accuracy loss —
# a sensible default on a memory-constrained laptop
model = WhisperModel(MODEL_SIZE, device="cpu", compute_type="int8")

# The voice UI fires overlapping requests by design (a periodic "live fill"
# re-transcription while still recording, plus a final one right after) and
# CTranslate2 has no internal queue for that — two calls in at once just
# split the same CPU between them, so both take roughly twice as long. On a
# CPU-only box that's enough to push a call past the frontend's timeout; the
# frontend then abandons it and fires the next one anyway, which now competes
# with the still-running orphaned call and is slower still, compounding with
# every retry until nothing ever finishes. A non-blocking lock turns
# "queue up and get slower forever" into "skip this cycle" instead — the next
# interim tick (or the final call, which the frontend already waits for the
# lock to free up before sending) picks it up cleanly.
_busy_lock = threading.Lock()


class TranscriberBusyError(RuntimeError):
    """Raised when a transcription is already in progress."""


def transcribe_audio(filepath: str) -> str:
    """
    Takes a path to an audio file (wav/mp3/webm/etc — faster-whisper handles
    most common formats via ffmpeg under the hood) and returns the
    transcribed text as a single string.

    Raises TranscriberBusyError if another transcription is already running,
    rather than blocking and competing with it for CPU.
    """
    if not _busy_lock.acquire(blocking=False):
        raise TranscriberBusyError("A transcription is already in progress.")
    try:
        # beam_size=1 (greedy decoding) instead of the default 5 — beam
        # search multiplies CPU cost by roughly the beam width for a small
        # accuracy gain that doesn't matter for short voice-command clips.
        # vad_filter skips the silence padding at the start/end of a mic
        # recording instead of running the model over it.
        segments, _info = model.transcribe(filepath, beam_size=1, vad_filter=True)
        text = " ".join(segment.text.strip() for segment in segments)
        return text.strip()
    finally:
        _busy_lock.release()
