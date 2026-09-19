"""Sistem çekmecesi (tray) simgesi; görseller Pillow ile çizilir, dosya gerekmez."""

from __future__ import annotations

import subprocess
import sys

STATE_COLORS = {
    "idle": (108, 117, 125),
    "recording": (225, 66, 66),
    "transcribing": (240, 173, 42),
}


def make_image(color: tuple[int, int, int], size: int = 64):
    from PIL import Image, ImageDraw

    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    pad = size // 8
    d.ellipse([pad, pad, size - pad, size - pad], fill=color + (255,))
    white = (255, 255, 255, 255)
    d.rounded_rectangle([26, 13, 38, 34], radius=6, fill=white)
    d.arc([21, 22, 43, 42], start=20, end=160, fill=white, width=3)
    d.line([32, 42, 32, 47], fill=white, width=3)
    d.line([26, 48, 38, 48], fill=white, width=3)
    return img


def open_config_file() -> None:
    from .config import config_path, load_config, save_config

    p = config_path()
    if not p.exists():
        save_config(load_config())
    if sys.platform == "win32":
        import os

        os.startfile(p)  # noqa: S606 - kullanıcının kendi config dosyası
    elif sys.platform == "darwin":
        subprocess.run(["open", str(p)], check=False)
    else:
        subprocess.run(["xdg-open", str(p)], check=False)


def build_icon(app):
    import pystray
    from pystray import Menu, MenuItem

    def status_text(_item):
        dot = {"idle": "⚪", "recording": "🔴", "transcribing": "🟠"}.get(app.state, "⚪")
        return f"{dot} {app.status_text[:60]}"

    def toggle_label(_item):
        return "⏹ Kaydı Durdur" if app.state == "recording" else "⏺ Kaydı Başlat"

    def open_window(_icon, _item):
        root = getattr(app, "_ui_root", None)
        if root is not None:
            try:
                root.after(0, lambda: (root.deiconify(), root.lift(), root.focus_force()))
            except Exception:
                pass

    menu = Menu(
        MenuItem(status_text, None, enabled=False),
        MenuItem(toggle_label, lambda icon, item: app.toggle()),
        MenuItem("🪟 Pencereyi Aç", open_window),
        MenuItem("⚙ Config dosyasını aç", lambda icon, item: open_config_file()),
        MenuItem("❌ Çıkış", lambda icon, item: app.quit()),
    )
    return pystray.Icon("dikte-plus", make_image(STATE_COLORS["idle"]), "Dikte+ - Hazır", menu)
