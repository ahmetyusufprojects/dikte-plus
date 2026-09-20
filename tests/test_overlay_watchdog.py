"""Hap bekçisi testleri — ekran gerektirir, yoksa atlanır.

Not: süreç başına tek Tk kökü kullanılır; birden çok Tk() aynı süreçte
"tcl_findLibrary" hatası verebiliyor.
"""

import pytest

from dikte_plus.ui_overlay import Overlay, OverlayWatchdog


@pytest.fixture(scope="module")
def tk_root():
    try:
        import tkinter as tk

        root = tk.Tk()
        root.withdraw()
    except Exception:
        pytest.skip("ekran yok")
    yield root
    try:
        root.destroy()
    except Exception:
        pass


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


def test_watchdog_recreates_dead_overlay(tk_root):
    app = FakeApp()
    wd = OverlayWatchdog(tk_root, app)
    assert wd.overlay is not None and wd.overlay.alive()
    wd.overlay.win.destroy()
    tk_root.update_idletasks()
    assert not wd.overlay.exists()
    wd.tick()
    assert wd.overlay is not None and wd.overlay.alive()


def test_watchdog_reshows_hidden_overlay(tk_root):
    app = FakeApp()
    wd = OverlayWatchdog(tk_root, app)
    first = wd.overlay
    assert first.alive()
    first.hide()
    assert not first.alive() and first.exists()
    wd.tick()
    assert wd.overlay is first  # aynı pencere, yeniden oluşturmadan
    assert first.alive()


def test_repin_does_not_raise(tk_root):
    ov = Overlay(tk_root, FakeApp())
    ov.repin()  # Windows'ta SetWindowPos, başka yerde no-op
    assert ov.alive()
    ov.win.destroy()
