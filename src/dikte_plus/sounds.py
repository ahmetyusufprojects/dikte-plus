"""Geri-bildirim sesleri: 4 hazır tema + özel WAV desteği.

Araştırma notu: iyi arayüz sesleri kısa, çok tonludur — başlatma için
yükselen iki/üç nota (örn. SFXMint'in "Gentle Two-Note Notification Chime"i),
durdurma için alçalan iki nota ("Call Ended Tone" kalıbı). Bu dosyadaki tüm
temalar bu kalıpları işlem içinde sentezler; dosya indirme, lisans derdi yok.

Kullanıcı kendi sesini de koyabilir: config klasörü altındaki `sounds/`
dizinine `start.wav`, `stop.wav`, `done.wav`, `error.wav` bırakmak yeterli.
Örn. Windows: %APPDATA%\\dikte-plus\\sounds\\start.wav
(CC0 kataloglar: https://sfxmint.com/category/ui , https://directory.audio/sound-effects/interface-ui)
"""

from __future__ import annotations

import math
import threading
import wave
from array import array
from pathlib import Path

_SR = 22050

# Tema kataloğu: ad -> açıklama (Türkçe). Sesler tembel üretilip önbelleğe alınır.
THEMES = {
    "soft": "Yumuşak — yükselen ikili (önerilen)",
    "bright": "Parlak — tiz, hızlı üçlü",
    "calm": "Sakin — pes, yavaş geçiş",
    "classic": "Klasik — tek ton (eski TypeLess sesi)",
}

_CACHE: dict[tuple[str, str], bytes] = {}


def _note(freq: float, ms: int, volume: float = 0.32) -> bytes:
    n = int(_SR * ms / 1000)
    fade = max(1, int(_SR * 0.008))
    buf = array("h")
    for i in range(n):
        env = min(1.0, i / fade, (n - i) / fade)
        buf.append(int(32767 * volume * env * math.sin(2 * math.pi * freq * i / _SR)))
    return buf.tobytes()


def _gap(ms: int) -> bytes:
    return b"\x00\x00" * int(_SR * ms / 1000)


def _seq(parts: list[tuple[float, int, float]]) -> bytes:
    out = bytearray()
    for i, (freq, ms, vol) in enumerate(parts):
        if i:
            out += _gap(25)
        out += _note(freq, ms, vol)
    return bytes(out)


def _build(theme: str, kind: str) -> bytes | None:
    if theme == "classic":
        return {
            "start": _note(880, 90),
            "stop": _note(520, 90),
            "done": _note(660, 120),
            "error": _note(200, 250),
        }.get(kind)
    if theme == "bright":
        table = {
            "start": [(784, 70, 0.30), (1047, 110, 0.30)],  # G5 -> C6
            "stop": [(1047, 70, 0.30), (784, 120, 0.30)],  # C6 -> G5
            "done": [(784, 70, 0.28), (988, 70, 0.28), (1175, 130, 0.30)],  # G5-B5-D6
        }
    elif theme == "calm":
        table = {
            "start": [(440, 140, 0.26), (659, 180, 0.26)],  # A4 -> E5
            "stop": [(659, 140, 0.26), (440, 200, 0.26)],  # E5 -> A4
            "done": [(523, 120, 0.24), (659, 120, 0.24), (784, 200, 0.26)],  # C5-E5-G5
        }
    else:  # soft (varsayılan)
        table = {
            "start": [(659, 90, 0.30), (880, 130, 0.30)],  # E5 -> A5
            "stop": [(880, 90, 0.30), (659, 150, 0.30)],  # A5 -> E5
            "done": [(659, 80, 0.28), (880, 80, 0.28), (1047, 150, 0.30)],  # E5-A5-C6
        }
    if kind == "error":
        return _note(196, 260, 0.32)
    spec = table.get(kind)
    return _seq(spec) if spec else None


def _pcm(theme: str, kind: str) -> bytes | None:
    key = (theme if theme in THEMES else "soft", kind)
    if key not in _CACHE:
        _CACHE[key] = _build(key[0], kind)
    return _CACHE[key]


def list_themes() -> dict[str, str]:
    return dict(THEMES)


def _custom_wav(sounds_dir: Path | None, kind: str) -> Path | None:
    if not sounds_dir:
        return None
    p = Path(sounds_dir) / f"{kind}.wav"
    return p if p.is_file() else None


def _play_wav_file(path: Path) -> None:
    def run():
        try:
            import sounddevice as sd

            with wave.open(str(path), "rb") as w:
                ch, sw, fr = w.getnchannels(), w.getsampwidth(), w.getframerate()
                raw = w.readframes(w.getnframes())
            with sd.RawOutputStream(samplerate=fr, channels=ch, dtype=f"int{sw * 8}") as s:
                s.write(raw)
        except Exception:
            try:  # sounddevice yoksa Windows bip'i
                import winsound

                winsound.PlaySound(str(path), winsound.SND_FILENAME | winsound.SND_ASYNC)
            except Exception:
                pass

    threading.Thread(target=run, daemon=True).start()


def play(kind: str, theme: str = "soft", sounds_dir: Path | str | None = None) -> None:
    """Bir geri-bildirim sesi çal. Özel WAV varsa onu, yoksa temayı kullanır."""
    custom = _custom_wav(Path(sounds_dir) if sounds_dir else None, kind)
    if custom is not None:
        _play_wav_file(custom)
        return
    data = _pcm(theme, kind)
    if not data:
        return

    def run():
        try:
            import sounddevice as sd

            with sd.RawOutputStream(samplerate=_SR, channels=1, dtype="int16") as stream:
                stream.write(data)
        except Exception:
            pass

    threading.Thread(target=run, daemon=True).start()
