"""Mikrofon yakalama ve WAV yardımcıları.

sounddevice bilerek tembel (lazy) import edilir; böylece config/CLI
komutları PortAudio kurulu olmayan makinede de çalışır.

TypeLess'ten fark: kayıt sırasında arayüzün VU-metre çizebilmesi için
`Recorder.level` anlık ses seviyesini (0.0-1.0) verir.
"""

from __future__ import annotations

import io
import threading
import wave
from array import array


class Recorder:
    def __init__(
        self,
        samplerate: int = 16000,
        device: int | str | None = None,
        max_seconds: int = 120,
    ):
        self.samplerate = samplerate
        self.device = device
        self._max_frames = max_seconds * samplerate
        self._chunks: list[bytes] = []
        self._frames = 0
        self._stream = None
        self._lock = threading.Lock()
        self._level = 0.0

    @property
    def recording(self) -> bool:
        return self._stream is not None

    @property
    def level(self) -> float:
        """0.0-1.0 arası anlık ses seviyesi (arayüz VU-metresi için)."""
        with self._lock:
            return self._level

    def start(self) -> None:
        import sounddevice as sd

        if self._stream is not None:
            return
        self._chunks = []
        self._frames = 0
        with self._lock:
            self._level = 0.0

        def callback(indata, frames, _time, _status):
            with self._lock:
                if self._frames < self._max_frames:
                    raw = bytes(indata)
                    self._chunks.append(raw)
                    self._frames += frames
                    try:
                        self._level = min(1.0, peak(raw) / 8000.0)
                    except Exception:
                        self._level = 0.0

        self._stream = sd.RawInputStream(
            samplerate=self.samplerate,
            channels=1,
            dtype="int16",
            device=self.device,
            callback=callback,
        )
        self._stream.start()

    def stop(self) -> bytes:
        """Yakalamayı durdur, o ana kadarki ham 16-bit mono PCM'i döndür."""
        stream, self._stream = self._stream, None
        if stream is not None:
            try:
                stream.stop()
                stream.close()
            except Exception:
                pass
        with self._lock:
            pcm = b"".join(self._chunks)
            self._chunks = []
            self._level = 0.0
        return pcm


def encode_wav(pcm: bytes, samplerate: int) -> bytes:
    buf = io.BytesIO()
    with wave.open(buf, "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(samplerate)
        w.writeframes(pcm)
    return buf.getvalue()


def peak(pcm: bytes) -> int:
    if len(pcm) < 2:
        return 0
    samples = array("h")
    samples.frombytes(pcm[: len(pcm) // 2 * 2])
    if not samples:
        return 0
    return max(abs(s) for s in samples)


def duration_seconds(pcm: bytes, samplerate: int) -> float:
    return len(pcm) / 2 / samplerate


def list_devices() -> str:
    import sounddevice as sd

    return str(sd.query_devices())
