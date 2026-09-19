"""Tamamen çevrimdışı transkripsiyon (opsiyonel faster-whisper)."""

from __future__ import annotations

import io
import tempfile
from pathlib import Path

from .base import Transcriber


class LocalWhisperTranscriber(Transcriber):
    def __init__(self, model: str = "large-v3-turbo", device: str = "auto", compute_type: str = "default"):
        self.model_name = model
        self.device = device
        self.compute_type = compute_type
        self._model = None

    def _ensure(self):
        if self._model is None:
            from faster_whisper import WhisperModel

            device = "cpu" if self.device == "auto" else self.device
            self._model = WhisperModel(self.model_name, device=device, compute_type=self.compute_type)
        return self._model

    def transcribe(self, audio: bytes, filename: str = "audio.wav", language: str = "", prompt: str = "") -> str:
        model = self._ensure()
        suffix = Path(filename).suffix or ".wav"
        with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as tmp:
            # audio zaten WAV kodlu gelebilir; değilse ham yaz.
            tmp.write(audio if audio[:4] == b"RIFF" else _wrap_wav(audio))
            tmp_path = tmp.name
        try:
            segments, _info = model.transcribe(
                tmp_path,
                language=language or None,
                initial_prompt=prompt or None,
                temperature=0.0,
            )
            return "".join(s.text for s in segments).strip()
        finally:
            try:
                Path(tmp_path).unlink(missing_ok=True)
            except Exception:
                pass


def _wrap_wav(pcm: bytes, samplerate: int = 16000) -> bytes:
    import wave

    buf = io.BytesIO()
    with wave.open(buf, "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(samplerate)
        w.writeframes(pcm)
    return buf.getvalue()
