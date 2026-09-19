"""Komut satırı: `dikte` argümansız çalışınca görsel uygulamayı başlatır."""

from __future__ import annotations

import argparse
import sys
import time


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(
        prog="dikte",
        description="Dikte+ : Groq Whisper ile görsel sesli dikte. Kısayola bas, konuş, metin imlece gelsin.",
    )
    sub = parser.add_subparsers(dest="command")

    p_run = sub.add_parser("run", help="uygulamayı başlat (varsayılan)")
    p_run.add_argument("--no-tray", action="store_true", help="tepsi simgesi olmadan çalış")
    p_run.add_argument("--no-gui", action="store_true", help="görsel arayüz olmadan (konsol) çalış")
    sub.add_parser("gui", help="ana pencereyle başlat (run ile aynı)")

    p_setup = sub.add_parser("setup", help="interaktif ilk kurulum")
    p_setup.add_argument("--provider", choices=["groq", "openai", "local", "custom"])
    p_setup.add_argument("--api-key")
    p_setup.add_argument("--hotkey")
    p_setup.add_argument("--mode", choices=["toggle", "hold"])
    p_setup.add_argument("--language")

    p_cfg = sub.add_parser("config", help="config'i göster veya: config set ANAHTAR DEĞER")
    p_cfg.add_argument("args", nargs="*")

    sub.add_parser("devices", help="mikrofonları listele")
    p_tr = sub.add_parser("transcribe", help="ses dosyasını yazıya dök (debug)")
    p_tr.add_argument("file")
    p_test = sub.add_parser("test", help="birkaç saniye kaydet, transkripti yazdır")
    p_test.add_argument("seconds", nargs="?", type=float, default=4.0)
    p_auto = sub.add_parser("autostart", help="oturum açılışında otomatik başlat")
    p_auto.add_argument("action", choices=["enable", "disable", "status"])

    args = parser.parse_args(argv)
    command = args.command or "run"

    if command == "run":
        cmd_run(no_tray=getattr(args, "no_tray", False), gui=not getattr(args, "no_gui", False))
    elif command == "gui":
        cmd_run(no_tray=False, gui=True)
    elif command == "setup":
        cmd_setup(args)
    elif command == "config":
        cmd_config(args.args)
    elif command == "devices":
        cmd_devices()
    elif command == "transcribe":
        cmd_transcribe(args.file)
    elif command == "test":
        cmd_test(args.seconds)
    elif command == "autostart":
        cmd_autostart(args.action)


def cmd_run(no_tray: bool, gui: bool = True) -> None:
    from .app import DikteApp
    from .config import load_config

    app = DikteApp(load_config())
    app.run(tray=not no_tray, gui=gui)


def _ask(prompt: str, default: str) -> str:
    shown = default if default else "yok"
    try:
        answer = input(f"{prompt} [{shown}]: ").strip()
    except EOFError:
        answer = ""
    return answer or default


def cmd_setup(args) -> None:
    from .config import load_config, resolve_api_key, save_config

    cfg = load_config()
    print("Dikte+ kurulum — aynen bırakmak için Enter'a basın.\n")

    cfg.provider = args.provider or _ask("Sağlayıcı (groq = ücretsiz & hızlı / openai / local = çevrimdışı / custom)", cfg.provider)
    if cfg.provider in ("groq", "openai", "custom"):
        has_key = bool(resolve_api_key(cfg.provider, cfg.api_key))
        state = "kayıtlı" if has_key else "yok"
        entered = args.api_key or _ask(f"API anahtarı ({state}; boş = mevcut/env)", "")
        if entered:
            cfg.api_key = entered
    if cfg.provider == "custom":
        cfg.base_url = _ask("OpenAI-uyumlu sunucu adresi", cfg.base_url or "http://localhost:8000/v1")
    cfg.hotkey = args.hotkey or _ask("Kısayol", cfg.hotkey)
    cfg.hotkey_mode = args.mode or _ask("Mod (toggle = bas-başlat/bas-durdur, hold = basılı-tut)", cfg.hotkey_mode)
    if args.language is not None:
        cfg.language = args.language
    else:
        cfg.language = _ask("Dil kodu, örn. tr (boş = otomatik)", cfg.language or "tr")

    path = save_config(cfg)
    print(f"\nKaydedildi: {path}")
    if cfg.provider in ("groq", "openai") and not resolve_api_key(cfg.provider, cfg.api_key):
        from .providers import KEY_URLS

        print(f"Hatırlatma: hâlâ API anahtarı lazım -> {KEY_URLS[cfg.provider]} (Groq ücretsiz, kredi kartı yok)")
    if sys.platform == "darwin":
        print("macOS: Terminal'e Mikrofon + Erişilebilirlik + Girdi İzleme izni verip yeniden başlatın.")
    print("Sıradaki: `dikte test` ile mikrofonu dene, sonra `dikte` ile başlat.")


def cmd_config(items: list[str]) -> None:
    import dataclasses
    import json

    from .config import config_path, load_config, save_config, set_value

    cfg = load_config()
    if not items:
        print(f"# {config_path()}")
        print(json.dumps(dataclasses.asdict(cfg), indent=2))
        return
    if items[0] == "set" and len(items) == 3:
        try:
            set_value(cfg, items[1], items[2])
        except KeyError as exc:
            raise SystemExit(str(exc.args[0])) from exc
        save_config(cfg)
        print(f"{items[1]} = {getattr(cfg, items[1])!r}")
        return
    raise SystemExit("kullanım: dikte config [set ANAHTAR DEĞER]")


def cmd_devices() -> None:
    from .audio import list_devices

    print(list_devices())


def cmd_transcribe(file: str) -> None:
    from pathlib import Path

    from .config import load_config
    from .formatting import build_prompt
    from .providers import create_transcriber

    cfg = load_config()
    path = Path(file)
    transcriber = create_transcriber(cfg)
    started = time.monotonic()
    text = transcriber.transcribe(
        path.read_bytes(), filename=path.name, language=cfg.language, prompt=build_prompt(cfg.prompt, cfg.vocabulary)
    )
    elapsed = time.monotonic() - started
    print(text)
    print(f"({elapsed:.1f} sn, {cfg.provider})", file=sys.stderr)


def cmd_test(seconds: float) -> None:
    from .audio import Recorder, duration_seconds, encode_wav, peak
    from .config import load_config
    from .formatting import build_prompt
    from .providers import create_transcriber

    cfg = load_config()
    recorder = Recorder(cfg.sample_rate, cfg.audio_device, max_seconds=int(seconds) + 5)
    print(f"{seconds:g} sn kayıt — şimdi konuş…")
    recorder.start()
    time.sleep(seconds)
    pcm = recorder.stop()
    level = peak(pcm)
    print(f"Yakalandı: {duration_seconds(pcm, cfg.sample_rate):.1f} sn (seviye {level})")
    if level < cfg.silence_peak:
        print("Uyarı: ses neredeyse sessiz — mikrofonu kontrol et (`dikte devices`).")
    transcriber = create_transcriber(cfg)
    started = time.monotonic()
    text = transcriber.transcribe(encode_wav(pcm, cfg.sample_rate), language=cfg.language, prompt=build_prompt(cfg.prompt, cfg.vocabulary))
    print(f"\nTranskript ({time.monotonic() - started:.1f} sn, {cfg.provider}):\n{text}")


def cmd_autostart(action: str) -> None:
    from . import autostart

    if action == "enable":
        print(f"Otomatik başlatma açıldı: {autostart.enable()}")
    elif action == "disable":
        print(f"Otomatik başlatma kapatıldı: {autostart.disable()}")
    else:
        enabled, path = autostart.status()
        print(f"Otomatik başlatma {'açık' if enabled else 'kapalı'} ({path})")
