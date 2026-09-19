"""Konuşma-metin arayüzü."""

from __future__ import annotations


class TranscriptionError(RuntimeError):
    pass


class Transcriber:
    def transcribe(
        self,
        audio: bytes,
        filename: str = "audio.wav",
        language: str = "",
        prompt: str = "",
    ) -> str:
        raise NotImplementedError
