"""
stt.py
Speech-to-text using faster-whisper. Loaded once at import time and kept
resident — these models are small enough (~75MB + ~500MB for 'tiny' +
'small') that they don't need swap/eviction logic like the LLMs do.
"""

import threading

from faster_whisper import WhisperModel

# Two models, traded off for two different jobs:
#  - The voice UI re-transcribes the ENTIRE growing clip on every "live
#    fill" tick while the user is still talking, so that call's cost grows
#    with how long they've been speaking — on a CPU-only box the 'small'
#    model falls behind the 1.3s tick interval within a few seconds, so
#    ticks queue up (see _busy_lock below) and the textbox visibly lags
#    behind speech, filling in late and all at once.
#  - 'tiny' is roughly 5-6x faster on CPU for a small accuracy cost that's
#    an acceptable trade for a live, provisional caption — the FINAL
#    transcription (after the mic stops) still uses 'small' for accuracy,
#    since that one only runs once and latency there matters far less.
INTERIM_MODEL_SIZE = "tiny"
FINAL_MODEL_SIZE = "small"

# compute_type="int8" keeps RAM/CPU usage low with minimal accuracy loss —
# a sensible default on a memory-constrained laptop
interim_model = WhisperModel(INTERIM_MODEL_SIZE, device="cpu", compute_type="int8")
final_model = WhisperModel(FINAL_MODEL_SIZE, device="cpu", compute_type="int8")

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
# interim lock to free up before sending) picks it up cleanly. Separate locks
# per model since they no longer share one and shouldn't block each other.
_interim_lock = threading.Lock()
_final_lock = threading.Lock()


class TranscriberBusyError(RuntimeError):
    """Raised when a transcription is already in progress."""


def _run(model: WhisperModel, lock: threading.Lock, filepath: str) -> str:
    if not lock.acquire(blocking=False):
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
        lock.release()


def transcribe_audio(filepath: str, fast: bool = False) -> str:
    """
    Takes a path to an audio file (wav/mp3/webm/etc — faster-whisper handles
    most common formats via ffmpeg under the hood) and returns the
    transcribed text as a single string.

    fast=True uses the smaller/quicker interim model (for the voice UI's
    live-fill re-transcription while still recording); fast=False (default)
    uses the larger, more accurate model for the one-shot final transcript.

    Raises TranscriberBusyError if another transcription on the same model
    is already running, rather than blocking and competing with it for CPU.
    """
    if fast:
        return _run(interim_model, _interim_lock, filepath)
    return _run(final_model, _final_lock, filepath)
