"""Oturum açılışında otomatik başlatma (Windows + macOS)."""

from __future__ import annotations

import sys
from pathlib import Path


def _win_startup_dir() -> Path:
    import os

    base = os.environ.get("APPDATA", str(Path.home() / "AppData" / "Roaming"))
    return Path(base) / "Microsoft" / "Windows" / "Start Menu" / "Programs" / "Startup"


def enable() -> str:
    if sys.platform == "win32":
        import sysconfig

        scripts = Path(sysconfig.get_path("scripts"))
        exe = scripts / "dikte.exe"
        target = exe if exe.exists() else Path(sys.executable)
        vbs = _win_startup_dir() / "DiktePlus.vbs"
        vbs.parent.mkdir(parents=True, exist_ok=True)
        vbs.write_text(
            f'CreateObject("Wscript.Shell").Run "{target}", 0, False\n', encoding="utf-8"
        )
        return str(vbs)
    if sys.platform == "darwin":
        plist = Path.home() / "Library" / "LaunchAgents" / "com.dikteplus.app.plist"
        plist.parent.mkdir(parents=True, exist_ok=True)
        plist.write_text(
            "<?xml version=\"1.0\" encoding=\"UTF-8\"?>\n"
            "<!DOCTYPE plist PUBLIC \"-//Apple//DTD PLIST 1.0//EN\" "
            "\"http://www.apple.com/DTDs/PropertyList-1.0.dtd\">\n"
            "<plist version=\"1.0\"><dict>\n"
            "<key>Label</key><string>com.dikteplus.app</string>\n"
            "<key>ProgramArguments</key><array><string>dikte</string></array>\n"
            "<key>RunAtLoad</key><true/>\n"
            "</dict></plist>\n",
            encoding="utf-8",
        )
        return str(plist)
    raise RuntimeError("otomatik başlatma yalnızca Windows ve macOS'ta desteklenir")


def disable() -> str:
    if sys.platform == "win32":
        vbs = _win_startup_dir() / "DiktePlus.vbs"
        if vbs.exists():
            vbs.unlink()
        return str(vbs)
    if sys.platform == "darwin":
        plist = Path.home() / "Library" / "LaunchAgents" / "com.dikteplus.app.plist"
        if plist.exists():
            plist.unlink()
        return str(plist)
    raise RuntimeError("otomatik başlatma yalnızca Windows ve macOS'ta desteklenir")


def status() -> tuple[bool, str]:
    if sys.platform == "win32":
        p = _win_startup_dir() / "DiktePlus.vbs"
        return p.exists(), str(p)
    if sys.platform == "darwin":
        p = Path.home() / "Library" / "LaunchAgents" / "com.dikteplus.app.plist"
        return p.exists(), str(p)
    return False, "desteklenmiyor"
