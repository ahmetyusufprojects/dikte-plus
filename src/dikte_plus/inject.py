"""Çözümlenen metni odağı olan uygulamaya ulaştırma."""

from __future__ import annotations

import sys
import threading
import time

import pyperclip


class Injector:
    PASTE_SETTLE = 0.15  # kısayolun modifier tuşları oturmadan Ctrl/Cmd+V gönderme
    RESTORE_DELAY = 1.0  # hedef uygulama panoyu okumadan eski panoyu geri yazma

    def __init__(self, mode: str = "paste", restore_clipboard: bool = True):
        self.mode = mode
        self.restore_clipboard = restore_clipboard
        self._kb = None
        self._restore_thread: threading.Thread | None = None

    def inject(self, text: str) -> None:
        if not text:
            return
        if self.mode == "type":
            self._controller().type(text)
        else:
            self._paste(text)

    def _controller(self):
        if self._kb is None:
            from pynput.keyboard import Controller

            self._kb = Controller()
        return self._kb

    def _paste(self, text: str) -> None:
        previous = None
        if self.restore_clipboard:
            try:
                previous = pyperclip.paste()
            except Exception:
                previous = None
        pyperclip.copy(text)
        time.sleep(self.PASTE_SETTLE)
        self._send_paste()
        if previous:
            self._restore_thread = threading.Thread(target=self._restore, args=(previous,), daemon=True)
            self._restore_thread.start()

    def _restore(self, previous: str) -> None:
        time.sleep(self.RESTORE_DELAY)
        try:
            pyperclip.copy(previous)
        except Exception:
            pass

    def _send_paste(self) -> None:
        from pynput.keyboard import Key

        kb = self._controller()
        modifier = Key.cmd if sys.platform == "darwin" else Key.ctrl
        with kb.pressed(modifier):
            kb.press("v")
            kb.release("v")
