"""Oturum açılışında otomatik başlatma (Windows + macOS).

Windows'ta konsolsuz (`dikte-gui.exe`) hedef + gizli VBS kullanılır,
böylece oturum açılışında terminal penceresi görünmez, yalnızca
tepsi simgesi + mini hap gelir.
"""

from __future__ import annotations

import sys
from pathlib import Path


def _win_startup_dir() -> Path:
    import os

    base = os.environ.get("APPDATA", str(Path.home() / "AppData" / "Roaming"))
    return Path(base) / "Microsoft" / "Windows" / "Start Menu" / "Programs" / "Startup"


def _win_target() -> tuple[str, str]:
    """(exe_yolu, argümanlar): konsolsuz başlatma hedefini seç."""
    import sysconfig

    scripts = Path(sysconfig.get_path("scripts"))
    for name in ("dikte-gui.exe", "dikte-gui", "dikte.exe"):
        exe = scripts / name
        if exe.exists():
            # dikte-gui konsol penceresi açmaz; dikte.exe açar ama VBS gizler.
            return str(exe), ""
    # Son çare: konsolsuz Python ile modül çalıştır
    pyw = Path(sys.executable).with_name("pythonw.exe")
    if pyw.exists():
        return str(pyw), " -m dikte_plus run"
    return str(Path(sys.executable)), " -m dikte_plus run"


def _vbs_text(primary_exe: str, primary_args: str, fallback_cmd: str) -> str:
    # NOT: VBScript'te iç tırnaklar """ ile yazılır. Kullanıcı adında boşluk
    # varsa (örn. "Ahmet Yusuf") tırnaksız yol 80070002 hatası verir.
    return (
        'Set sh = CreateObject("Wscript.Shell")\n'
        'Set fs = CreateObject("Scripting.FileSystemObject")\n'
        f'If fs.FileExists("{primary_exe}") Then\n'
        f'  sh.Run """{primary_exe}"""{primary_args}, 0, False\n'
        "Else\n"
        f'  sh.Run "{fallback_cmd}", 0, False\n'
        "End If\n"
    )


def enable(startup_dir: Path | None = None) -> str:
    if sys.platform == "win32":
        exe, args = _win_target()
        # Açılışta sessiz başla: ana pencere gizli, yalnızca tepsi + hap.
        # (args zaten boş veya boşlukla başlıyor; sondaki bayrak boşlukla eklenir)
        args = args + " --minimized"
        # Yedek: exe silinirse PATH üzerinden konsolsuz Python ile çalıştır
        fallback_cmd = "pythonw -m dikte_plus run --minimized"
        vbs = (startup_dir or _win_startup_dir()) / "DiktePlus.vbs"
        vbs.parent.mkdir(parents=True, exist_ok=True)
        # 0 = gizli pencere, False = bekleme. Konsolsuz exe ile birleşince
        # açılışta hiç terminal görünmez.
        vbs.write_text(_vbs_text(exe, args, fallback_cmd), encoding="utf-8")
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
