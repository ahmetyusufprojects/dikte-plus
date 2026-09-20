"""Hap bekçisi testleri — ekran gerektirir, yoksa atlanır."""

import pytest

from dikte_plus.ui_overlay import OverlayWatchdog

try:
    import tkinter as tk

    _root = tk.Tk()
    _root.withdraw()
    _root.destroy()
    HAS_DISPLAY = True
except Exception:
    HAS_DISPLAY = False

needs_display = pytest.mark.skipif(not HAS_DISPLAY, reason="ekran yok")


class FakeCfg:
    overlay_enabled = True
    overlay_alpha = 1.0
    overlay_position = "top-center"


class FakeApp:
    cfg = FakeCfg()
    state = "idle"
    status_text = "Hazır"
    level = 0.0

    def elapsed(self):
        return 0.0

    def toggle(self):
        pass

    def log(self, msg):
        pass


@needs_display
def test_watchdog_recreates_dead_overlay():
    import tkinter as tk

    root = tk.Tk()
    root.withdraw()
    try:
        app = FakeApp()
        wd = OverlayWatchdog(root, app)
        assert wd.overlay is not None and wd.overlay.alive()
        wd.overlay.win.destroy()
        root.update_idletasks()
        assert not wd.overlay.exists()
        wd.tick()
        assert wd.overlay is not None and wd.overlay.alive()
    finally:
        root.destroy()


@needs_display
def test_watchdog_reshows_hidden_overlay():
    import tkinter as tk

    root = tk.Tk()
    root.withdraw()
    try:
        app = FakeApp()
        wd = OverlayWatchdog(root, app)
        first = wd.overlay
        assert first.alive()
        first.hide()
        assert not first.alive() and first.exists()
        wd.tick()
        assert wd.overlay is first  # aynı pencere, yeniden oluşturmadan
        assert first.alive()
    finally:
        root.destroy()


@needs_display
def test_repin_does_not_raise():
    import tkinter as tk

    root = tk.Tk()
    root.withdraw()
    try:
        from dikte_plus.ui_overlay import Overlay

        ov = Overlay(root, FakeApp())
        ov.repin()  # Windows'ta SetWindowPos, başka yerde no-op
        ov.win.destroy()
    finally:
        root.destroy()
