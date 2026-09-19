"""Kısa geri-bildirim tonları; dosyasız, işlem içinde üretilir."""

from __future__ import annotations

import math
import threading
from array import array

_SR = 22050


def _tone(freq: float, ms: int, volume: float = 0.35) -> bytes:
    n = int(_SR * ms / 1000)
    fade = max(1, int(_SR * 0.005))
    buf = array("h")
    for i in range(n):
        env = min(1.0, i / fade, (n - i) / fade)
        buf.append(int(32767 * volume * env * math.sin(2 * math.pi * freq * i / _SR)))
    return buf.tobytes()


_TONES = {
    "start": _tone(880, 90),
    "stop": _tone(520, 90),
    "error": _tone(200, 250),
    "done": _tone(660, 120),
}


def play(kind: str) -> None:
    data = _TONES.get(kind)
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
