from ..config import Config, resolve_api_key
from .base import Transcriber, TranscriptionError
from .cloud import GROQ_BASE, OPENAI_BASE, OpenAICompatTranscriber

DEFAULT_MODELS = {
    "groq": "whisper-large-v3",
    "openai": "gpt-4o-transcribe",
    "custom": "whisper-1",
    "local": "large-v3-turbo",
}

KEY_URLS = {
    "groq": "https://console.groq.com/keys",
    "openai": "https://platform.openai.com/api-keys",
}

_CLOUD_BASES = {"groq": GROQ_BASE, "openai": OPENAI_BASE}


def create_transcriber(cfg: Config) -> Transcriber:
    provider = cfg.provider
    model = cfg.model or DEFAULT_MODELS.get(provider, "")
    if provider == "local":
        from .local import LocalWhisperTranscriber

        return LocalWhisperTranscriber(model, device=cfg.local_device, compute_type=cfg.local_compute_type)
    if provider in ("groq", "openai", "custom"):
        base = _CLOUD_BASES.get(provider) or cfg.base_url
        if not base:
            raise TranscriptionError(
                "provider 'custom' için base_url gerekli, örn. "
                "`dikte config set base_url http://localhost:8000/v1`"
            )
        key = resolve_api_key(provider, cfg.api_key)
        if not key and provider != "custom":
            raise TranscriptionError(
                f"{provider} için API anahtarı yok. {KEY_URLS[provider]} adresinden alın, "
                f"sonra `dikte setup` çalıştırın veya {provider.upper()}_API_KEY tanımlayın."
            )
        return OpenAICompatTranscriber(provider, base, key, model)
    raise TranscriptionError(f"bilinmeyen sağlayıcı {provider!r} (groq, openai, local, custom kullanın)")


__all__ = [
    "Transcriber",
    "TranscriptionError",
    "OpenAICompatTranscriber",
    "create_transcriber",
    "DEFAULT_MODELS",
    "KEY_URLS",
    "GROQ_BASE",
    "OPENAI_BASE",
]
