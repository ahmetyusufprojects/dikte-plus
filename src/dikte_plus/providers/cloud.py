"""Herhangi bir OpenAI-uyumlu /audio/transcriptions uç noktası üzerinden STT.

Groq, OpenAI ve kendi sunucularınızı (speaches, whisper.cpp server,
LocalAI, ...) kapsar. Groq ücretsiz katmanıyla varsayılan olarak çalışır.
"""

from __future__ import annotations

import mimetypes

import requests

from .base import Transcriber, TranscriptionError

GROQ_BASE = "https://api.groq.com/openai/v1"
OPENAI_BASE = "https://api.openai.com/v1"

_HINTS = {
    401: "API anahtarı reddedildi; `dikte setup` çalıştırın veya env değişkenini kontrol edin",
    413: "kayıt çok büyük; config'de max_seconds değerini düşürün",
    429: "hız limiti; biraz bekleyip tekrar deneyin",
}


class OpenAICompatTranscriber(Transcriber):
    def __init__(self, name: str, base_url: str, api_key: str, model: str, timeout: float = 120.0):
        self.name = name
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key
        self.model = model
        self.timeout = timeout

    def transcribe(
        self,
        audio: bytes,
        filename: str = "audio.wav",
        language: str = "",
        prompt: str = "",
    ) -> str:
        data = {"model": self.model, "response_format": "json", "temperature": "0"}
        if language:
            data["language"] = language
        if prompt:
            data["prompt"] = prompt
        mime = mimetypes.guess_type(filename)[0] or "audio/wav"
        try:
            resp = requests.post(
                f"{self.base_url}/audio/transcriptions",
                headers={"Authorization": f"Bearer {self.api_key}"},
                data=data,
                files={"file": (filename, audio, mime)},
                timeout=self.timeout,
            )
        except requests.RequestException as exc:
            raise TranscriptionError(f"{self.name}: ağ hatası: {exc}") from exc
        if resp.status_code != 200:
            hint = _HINTS.get(resp.status_code)
            raise TranscriptionError(
                f"{self.name} HTTP {resp.status_code} döndürdü"
                + (f" ({hint})" if hint else "")
                + f": {resp.text[:300]}"
            )
        return (resp.json().get("text") or "").strip()
