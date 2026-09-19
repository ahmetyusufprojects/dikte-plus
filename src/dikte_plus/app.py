"""Uygulama çekirdeği: kısayol -> kayıt -> transkripsiyon -> biçimlendirme -> yapıştırma.

TypeLess ile aynı boru hattı, ama durum değişiklikleri arayüzün okuyabilmesi için
`status_text`, `last_text`, `last_error`, `history`, `record_started` alanlarında
yayınlanır. Arayüz bu alanları 100 ms'de bir yoklar (thread-safe, basit, sağlam).
"""

from __future__ import annotations

import threading
import time
from collections import deque

from . import sounds
from .audio import Recorder, duration_seconds, encode_wav, peak
from .cleanup import cleanup_text
from .config import Config, config_path
from .formatting import build_prompt, format_text
from .hotkey import HotkeyListener
from .inject import Injector
from .providers import create_transcriber

IDLE, RECORDING, TRANSCRIBING = "idle", "recording", "transcribing"

STATUS_TR = {
    "idle": "Hazır — kısayola basıp konuşun",
    "recording": "● Kaydediliyor… tekrar basınca durur",
    "transcribing": "⏳ Yazıya dökülüyor…",
}


class DikteApp:
    def __init__(self, cfg: Config):
        self.cfg = cfg
        self.state = IDLE
        self.status_text = STATUS_TR[IDLE]
        self.last_text = ""
        self.last_error = ""
        self.history: deque[str] = deque(maxlen=cfg.history_size or 20)
        self.record_started = 0.0
        self.record_seconds = 0.0
        self.recorder = Recorder(
            samplerate=cfg.sample_rate, device=cfg.audio_device, max_seconds=cfg.max_seconds
        )
        self.injector = Injector(cfg.injection, cfg.restore_clipboard)
        self._transcriber = None
        self._transcriber_lock = threading.Lock()
        self._state_lock = threading.Lock()
        self._icon = None
        self._listener = None
        self._timer: threading.Timer | None = None
        self._stop_event = threading.Event()
        self._ui_root = None

    def log(self, msg: str) -> None:
        print(f"[dikte+] {msg}", flush=True)

    def _play(self, kind: str) -> None:
        if self.cfg.sounds:
            try:
                from .config import sounds_dir

                sounds.play(kind, theme=getattr(self.cfg, "sound_theme", "soft"), sounds_dir=sounds_dir())
            except Exception:
                sounds.play(kind)

    @property
    def level(self) -> float:
        try:
            return self.recorder.level if self.state == RECORDING else 0.0
        except Exception:
            return 0.0

    def elapsed(self) -> float:
        if self.state == RECORDING and self.record_started:
            return time.monotonic() - self.record_started
        return self.record_seconds

    def _set_state(self, state: str, status: str = "", error: str = "") -> None:
        self.state = state
        if status:
            self.status_text = status
        else:
            self.status_text = STATUS_TR.get(state, state)
        if error:
            self.last_error = error
        if self._icon is not None:
            try:
                from .tray import STATE_COLORS, make_image

                self._icon.icon = make_image(STATE_COLORS[state])
                self._icon.title = f"Dikte+ - {self.status_text}"
                self._icon.update_menu()
            except Exception:
                pass

    def get_transcriber(self):
        with self._transcriber_lock:
            if self._transcriber is None:
                self._transcriber = create_transcriber(self.cfg)
            return self._transcriber

    def on_activate(self) -> None:
        if self.cfg.hotkey_mode == "hold":
            self.start_recording()
        else:
            self.toggle()

    def on_deactivate(self) -> None:
        self.stop_recording()

    def toggle(self, *_args) -> None:
        if self.state == RECORDING:
            self.stop_recording()
        elif self.state == IDLE:
            self.start_recording()

    def start_recording(self, *_args) -> None:
        with self._state_lock:
            if self.state != IDLE:
                return
            try:
                self.recorder.start()
            except Exception as exc:
                self._set_state(IDLE, error=f"Mikrofon açılamadı: {exc}")
                self.log(f"mikrofon açılamadı: {exc}")
                self._play("error")
                return
            self.record_started = time.monotonic()
            self.record_seconds = 0.0
            self.last_error = ""
            self._set_state(RECORDING)
        self._play("start")
        self.log(f"kayıt başladı (kısayol: {self.cfg.hotkey})")
        self._timer = threading.Timer(self.cfg.max_seconds, self.stop_recording)
        self._timer.daemon = True
        self._timer.start()

    def stop_recording(self, *_args) -> None:
        with self._state_lock:
            if self.state != RECORDING:
                return
            self.record_seconds = time.monotonic() - self.record_started
            self._set_state(TRANSCRIBING)
        if self._timer is not None:
            self._timer.cancel()
            self._timer = None
        pcm = self.recorder.stop()
        self._play("stop")
        self.log(f"kayıt durdu ({self.record_seconds:.1f} sn), yazıya dökülüyor…")
        threading.Thread(target=self._process, args=(pcm,), daemon=True).start()

    def _process(self, pcm: bytes) -> None:
        try:
            secs = duration_seconds(pcm, self.cfg.sample_rate)
            if secs < self.cfg.min_seconds or peak(pcm) < self.cfg.silence_peak:
                msg = f"Sessizlik atlandı ({secs:.1f} sn) — mikrofonu kontrol edin"
                self.log(msg)
                self._set_state(IDLE, status=msg)
                return
            wav = encode_wav(pcm, self.cfg.sample_rate)
            prompt = build_prompt(self.cfg.prompt, self.cfg.vocabulary)
            text = self.get_transcriber().transcribe(wav, language=self.cfg.language, prompt=prompt)
            if self.cfg.cleanup:
                text = cleanup_text(text, self.cfg)
            text = format_text(text, self.cfg.replacements, self.cfg.append_space)
            if text:
                self.injector.inject(text)
                self.last_text = text
                self.history.appendleft(text)
                done = f"Yapıştırıldı ({secs:.1f} sn ses → {len(text)} karakter)"
                self.log(done)
                self._set_state(IDLE, status=done)
                self._play("done")
            else:
                self._set_state(IDLE, status="Boş transkript — tekrar deneyin")
                self.log("boş transkript")
        except Exception as exc:
            self._play("error")
            self.log(f"hata: {exc}")
            self._set_state(IDLE, status=f"Hata: {exc}", error=str(exc))
        finally:
            if self.state == TRANSCRIBING:
                self._set_state(IDLE)

    def warm(self) -> None:
        try:
            self.get_transcriber()
        except Exception as exc:
            self.log(f"sağlayıcı kontrolü başarısız: {exc}")
            self.last_error = str(exc)

    def quit(self, *_args) -> None:
        if self._listener is not None:
            try:
                self._listener.stop()
            except Exception:
                pass
        self._stop_event.set()
        if self._icon is not None:
            try:
                self._icon.stop()
            except Exception:
                pass
        if self._ui_root is not None:
            try:
                self._ui_root.quit()
            except Exception:
                pass

    def run(self, tray: bool = True, gui: bool = True) -> None:
        mode_hint = "basılı tut" if self.cfg.hotkey_mode == "hold" else "bas-başlat / bas-durdur"
        self.log(f"sağlayıcı={self.cfg.provider} model={self.cfg.model or '(varsayılan)'}")
        self.log(f"kısayol: {self.cfg.hotkey} ({mode_hint})")
        self.log(f"config: {config_path()}")
        self._listener = HotkeyListener(self.cfg.hotkey, self.cfg.hotkey_mode, self.on_activate, self.on_deactivate)
        try:
            self._listener.start()
        except Exception as exc:
            self.log(f"kısayol dinleyici başlatılamadı: {exc}")
        threading.Thread(target=self.warm, daemon=True).start()

        if gui:
            try:
                from .ui_main import run_gui

                run_gui(self, with_tray=tray)
                return
            except Exception as exc:
                self.log(f"GUI açılamadı ({exc}); konsol modunda devam")
        if tray:
            try:
                from .tray import build_icon

                self._icon = build_icon(self)
            except Exception as exc:
                self.log(f"tray kullanılamıyor ({exc}); konsol modu (çıkış: Ctrl+C)")
        if self._icon is not None:
            self._icon.run()
        else:
            try:
                self._stop_event.wait()
            except KeyboardInterrupt:
                pass
        self.quit()
