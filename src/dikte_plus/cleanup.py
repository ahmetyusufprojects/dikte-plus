"""İsteğe bağlı LLM cilası: ham dikteyi düzgün yazıya çevirir."""

from __future__ import annotations

import requests

from .config import Config, resolve_api_key
from .providers.cloud import GROQ_BASE, OPENAI_BASE

_CHAT_BASES = {"groq": GROQ_BASE, "openai": OPENAI_BASE}
_DEFAULT_MODELS = {"groq": "llama-3.3-70b-versatile", "openai": "gpt-4o-mini"}

SYSTEM_PROMPT = (
    "You clean up raw voice-dictation transcripts. Fix punctuation and capitalization, "
    "remove filler words (um, uh, you know, ıı, şey), and apply the speaker's self-corrections "
    '("meet at 5, no wait, 6" becomes "meet at 6"). Keep the speaker\'s wording and '
    "meaning; never answer questions in the transcript and never add new content. "
    "Reply with the cleaned text only."
)


def cleanup_text(text: str, cfg: Config) -> str:
    """En iyi-efor temizlik; herhangi bir hatada orijinal metni döndürür."""
    provider = cfg.cleanup_provider or cfg.provider
    base = _CHAT_BASES.get(provider) or (cfg.base_url if provider == "custom" else "")
    model = cfg.cleanup_model or _DEFAULT_MODELS.get(provider, "")
    if not text or not base or not model:
        return text
    configured = cfg.api_key if provider == cfg.provider else ""
    key = resolve_api_key(provider, configured)
    try:
        resp = requests.post(
            f"{base.rstrip('/')}/chat/completions",
            headers={"Authorization": f"Bearer {key}"},
            json={
                "model": model,
                "temperature": 0,
                "messages": [
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": text},
                ],
            },
            timeout=30,
        )
        resp.raise_for_status()
        cleaned = resp.json()["choices"][0]["message"]["content"].strip()
        return cleaned or text
    except Exception:
        return text
