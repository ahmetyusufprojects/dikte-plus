"""Her transkripte uygulanan metin son-işlemesi."""

from __future__ import annotations

import re


def format_text(
    text: str,
    replacements: dict[str, str] | None = None,
    append_space: bool = True,
) -> str:
    t = (text or "").strip()
    if not t:
        return ""
    for src, dst in (replacements or {}).items():
        if not src:
            continue
        t = re.sub(rf"\b{re.escape(src)}\b", dst, t, flags=re.IGNORECASE)
    if append_space:
        t += " "
    return t


def build_prompt(prompt: str = "", vocabulary: list[str] | None = None) -> str:
    """Kullanıcı bağlamı + kelime listesini Whisper tarzı ön-istemde birleştir."""
    parts = []
    if prompt:
        parts.append(prompt.strip())
    if vocabulary:
        parts.append("Vocabulary: " + ", ".join(vocabulary) + ".")
    return " ".join(parts)
