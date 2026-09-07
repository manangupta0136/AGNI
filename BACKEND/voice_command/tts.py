"""
tts.py
Text-to-speech using Piper. The voice model is loaded once at import time
and kept resident — like faster-whisper, this is small enough (~60MB) that
it doesn't need swap/eviction logic.
"""

import io
import wave
from pathlib import Path
from piper import PiperVoice

VOICE_MODEL_PATH = Path(__file__).parent / "voices" / "en_US-lessac-high.onnx"

voice = PiperVoice.load(str(VOICE_MODEL_PATH))


def synthesize_speech(text: str) -> bytes:
    buffer = io.BytesIO()
    with wave.open(buffer, "wb") as wav_file:
        wav_file.setnchannels(1)                      # Piper outputs mono audio
        wav_file.setsampwidth(2)                        # 16-bit PCM = 2 bytes per sample
        wav_file.setframerate(voice.config.sample_rate)  # matches the voice model's actual rate
        for chunk in voice.synthesize(text):
            wav_file.writeframes(chunk.audio_int16_bytes)
    return buffer.getvalue()