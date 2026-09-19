"""Yapılandırma: platform config dizininde JSON olarak saklanan düz dataclass.

TypeLess ile aynı anahtar adları korunur, böylece mevcut
`%APPDATA%\\typeless\\config.json` içindeki API anahtarı kolayca taşınabilir.
"""

from __future__ import annotations

import dataclasses
import json
import os
from dataclasses import dataclass, field
from pathlib import Path

import platformdirs

APP_NAME = "dikte-plus"
LEGACY_APP_NAME = "typeless"

ENV_KEYS = {"groq": "GROQ_API_KEY", "openai": "OPENAI_API_KEY"}


def resolve_api_key(provider: str, configured: str = "") -> str:
    if configured:
        return configured
    env_name = ENV_KEYS.get(provider, "")
    value = os.environ.get(env_name, "") if env_name else ""
    return value or os.environ.get("TYPELESS_API_KEY", "") or os.environ.get("DIKTE_API_KEY", "")


@dataclass
class Config:
    # Konuşma-metin sağlayıcısı: "groq" (ücretsiz katman, varsayılan), "openai", "local", "custom"
    provider: str = "groq"
    model: str = ""  # boş = sağlayıcı varsayılanı
    api_key: str = ""  # boş = env'den oku (GROQ_API_KEY / OPENAI_API_KEY / DIKTE_API_KEY)
    base_url: str = ""  # sadece "custom" sağlayıcı için
    language: str = ""  # ISO kodu, örn. "tr"; boş = otomatik algıla
    prompt: str = ""  # modele verilen ek bağlam (isimler, jargon)
    vocabulary: list[str] = field(default_factory=list)
    replacements: dict[str, str] = field(default_factory=dict)

    hotkey: str = "ctrl+shift+space"
    hotkey_mode: str = "toggle"  # "toggle" = bas-bırak, "hold" = basılı tut
    injection: str = "paste"  # "paste" (hızlı) veya "type" (karakter karakter)
    restore_clipboard: bool = True
    append_space: bool = True

    # İsteğe bağlı LLM temizliği: dolgu kelimelerini atar, kendi düzeltmelerini uygular
    cleanup: bool = False
    cleanup_provider: str = ""
    cleanup_model: str = ""

    sounds: bool = True
    audio_device: int | str | None = None
    sample_rate: int = 16000
    max_seconds: int = 120
    min_seconds: float = 0.3
    silence_peak: int = 500

    local_device: str = "auto"
    local_compute_type: str = "default"

    # --- Görsel arayüz tercihleri (TypeLess'te yok, Dikte+'ta yeni) ---
    overlay_enabled: bool = True
    overlay_position: str = "top-center"  # "top-center" veya "bottom-right"
    overlay_alpha: float = 0.8  # 0.4 (çok saydam) - 1.0 (opak)
    history_size: int = 20

    def resolve_api_key(self) -> str:
        return resolve_api_key(self.provider, self.api_key)


def config_path() -> Path:
    return Path(platformdirs.user_config_dir(APP_NAME)) / "config.json"


def legacy_config_path() -> Path:
    return Path(platformdirs.user_config_dir(LEGACY_APP_NAME)) / "config.json"


def load_config(path: Path | None = None) -> Config:
    p = path or config_path()
    if not p.exists():
        # TypeLess'ten tek seferlik taşıma: API anahtarını yeniden yazdırmayalım.
        legacy = legacy_config_path()
        if legacy.exists():
            try:
                data = json.loads(legacy.read_text(encoding="utf-8"))
                known = {f.name for f in dataclasses.fields(Config)}
                return Config(**{k: v for k, v in data.items() if k in known})
            except Exception:
                pass
        return Config()
    data = json.loads(p.read_text(encoding="utf-8"))
    known = {f.name for f in dataclasses.fields(Config)}
    return Config(**{k: v for k, v in data.items() if k in known})


def save_config(cfg: Config, path: Path | None = None) -> Path:
    p = path or config_path()
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(dataclasses.asdict(cfg), indent=2) + "\n", encoding="utf-8")
    return p


def set_value(cfg: Config, key: str, raw: str) -> None:
    """CLI string'inden tek ayar değiştir; JSON değerler parse edilir."""
    known = {f.name for f in dataclasses.fields(Config)}
    if key not in known:
        raise KeyError(f"bilinmeyen ayar {key!r}; geçerli anahtarlar: {', '.join(sorted(known))}")
    try:
        value = json.loads(raw)
    except json.JSONDecodeError:
        value = raw
    setattr(cfg, key, value)
