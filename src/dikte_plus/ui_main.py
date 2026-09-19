"""Ana pencere + ayarlar + GUI başlatıcı (yalnızca tkinter, ek bağımlılık yok)."""

from __future__ import annotations

import threading
import tkinter as tk
from tkinter import messagebox, ttk

from . import autostart
from .config import load_config, save_config

DOT_COLOR = {"idle": "#9aa0a6", "recording": "#ff5252", "transcribing": "#ffb74d"}


class SettingsDialog(tk.Toplevel):
    def __init__(self, parent, app):
        super().__init__(parent)
        self.app = app
        self.title("Dikte+ Ayarlar")
        self.resizable(False, False)
        cfg = app.cfg
        self.vars = {
            "provider": tk.StringVar(value=cfg.provider),
            "api_key": tk.StringVar(value=cfg.api_key),
            "language": tk.StringVar(value=cfg.language),
            "hotkey": tk.StringVar(value=cfg.hotkey),
            "hotkey_mode": tk.StringVar(value=cfg.hotkey_mode),
            "cleanup": tk.BooleanVar(value=cfg.cleanup),
            "sounds": tk.BooleanVar(value=cfg.sounds),
            "overlay_enabled": tk.BooleanVar(value=cfg.overlay_enabled),
        }
        frm = ttk.Frame(self, padding=14)
        frm.pack(fill="both", expand=True)
        row = 0
        ttk.Label(frm, text="Sağlayıcı (Groq ücretsiz):").grid(row=row, column=0, sticky="w", pady=3)
        ttk.Combobox(frm, textvariable=self.vars["provider"], values=["groq", "openai", "local", "custom"], width=28).grid(
            row=row, column=1, pady=3
        )
        row += 1
        ttk.Label(frm, text="API anahtarı:").grid(row=row, column=0, sticky="w", pady=3)
        ttk.Entry(frm, textvariable=self.vars["api_key"], show="*", width=30).grid(row=row, column=1, pady=3)
        row += 1
        ttk.Label(frm, text="Dil (tr / en / boş=oto):").grid(row=row, column=0, sticky="w", pady=3)
        ttk.Entry(frm, textvariable=self.vars["language"], width=30).grid(row=row, column=1, pady=3)
        row += 1
        ttk.Label(frm, text="Kısayol:").grid(row=row, column=0, sticky="w", pady=3)
        ttk.Entry(frm, textvariable=self.vars["hotkey"], width=30).grid(row=row, column=1, pady=3)
        row += 1
        ttk.Label(frm, text="Kısayol modu:").grid(row=row, column=0, sticky="w", pady=3)
        ttk.Combobox(frm, textvariable=self.vars["hotkey_mode"], values=["toggle", "hold"], width=28).grid(
            row=row, column=1, pady=3
        )
        row += 1
        ttk.Checkbutton(frm, text="LLM cilası (dolgu kelimelerini temizle)", variable=self.vars["cleanup"]).grid(
            row=row, column=0, columnspan=2, sticky="w", pady=3
        )
        row += 1
        ttk.Checkbutton(frm, text="Sesli bildirim (bip)", variable=self.vars["sounds"]).grid(
            row=row, column=0, columnspan=2, sticky="w", pady=3
        )
        row += 1
        ttk.Checkbutton(frm, text="Mini göstergeyi (hap) göster", variable=self.vars["overlay_enabled"]).grid(
            row=row, column=0, columnspan=2, sticky="w", pady=3
        )
        row += 1
        btn = ttk.Frame(frm)
        btn.grid(row=row, column=0, columnspan=2, pady=(10, 0))
        ttk.Button(btn, text="Kaydet", command=self._save).pack(side="left", padx=4)
        ttk.Button(btn, text="Vazgeç", command=self.destroy).pack(side="left", padx=4)
        ttk.Label(
            frm,
            text="Not: kısayol / mikrofon değişikliği için uygulamayı yeniden başlatın.",
            foreground="gray",
        ).grid(row=row + 1, column=0, columnspan=2, pady=(8, 0))

    def _save(self):
        cfg = self.app.cfg
        cfg.provider = self.vars["provider"].get().strip() or "groq"
        cfg.api_key = self.vars["api_key"].get().strip()
        cfg.language = self.vars["language"].get().strip()
        cfg.hotkey = self.vars["hotkey"].get().strip() or "ctrl+shift+space"
        cfg.hotkey_mode = self.vars["hotkey_mode"].get().strip() or "toggle"
        cfg.cleanup = bool(self.vars["cleanup"].get())
        cfg.sounds = bool(self.vars["sounds"].get())
        cfg.overlay_enabled = bool(self.vars["overlay_enabled"].get())
        save_config(cfg)
        messagebox.showinfo("Dikte+", "Ayarlar kaydedildi.")
        self.destroy()


class MainWindow:
    def __init__(self, root: tk.Tk, app):
        self.root = root
        self.app = app
        root.title("Dikte+ — Groq ile sesli yazı")
        root.geometry("500x620")
        root.minsize(460, 560)

        top = ttk.Frame(root, padding=12)
        top.pack(fill="x")
        self.canvas_dot = tk.Canvas(top, width=22, height=22, highlightthickness=0)
        self.canvas_dot.pack(side="left")
        self._dot = self.canvas_dot.create_oval(3, 3, 19, 19, fill=DOT_COLOR["idle"], outline="")
        txt = ttk.Frame(top)
        txt.pack(side="left", fill="x", expand=True, padx=(8, 0))
        self.status_lbl = ttk.Label(txt, text="Hazır", font=("Segoe UI", 10, "bold"))
        self.status_lbl.pack(anchor="w")
        self.sub_lbl = ttk.Label(txt, text="", foreground="gray", font=("Segoe UI", 9))
        self.sub_lbl.pack(anchor="w")
        self.timer_lbl = ttk.Label(top, text="", font=("Segoe UI", 11, "bold"))
        self.timer_lbl.pack(side="right")

        self.level = ttk.Progressbar(root, maximum=100, length=200)
        self.level.pack(fill="x", padx=12, pady=(0, 8))

        self.mic_btn = ttk.Button(root, text="🎤  Kaydı Başlat", command=self.app.toggle)
        self.mic_btn.pack(fill="x", padx=12, pady=4)

        ttk.Label(root, text="Son metin:").pack(anchor="w", padx=12, pady=(8, 0))
        self.text = tk.Text(root, height=5, wrap="word", font=("Segoe UI", 10))
        self.text.pack(fill="x", padx=12, pady=4)
        row1 = ttk.Frame(root)
        row1.pack(fill="x", padx=12)
        ttk.Button(row1, text="📋 Kopyala", command=self._copy).pack(side="left", padx=(0, 6))
        ttk.Button(row1, text="📥 İmlece Tekrar Yapıştır", command=self._repaste).pack(side="left")

        ttk.Label(root, text="Geçmiş:").pack(anchor="w", padx=12, pady=(8, 0))
        self.hist = tk.Listbox(root, height=7, font=("Segoe UI", 9))
        self.hist.pack(fill="both", expand=True, padx=12, pady=4)

        bar = ttk.Frame(root, padding=10)
        bar.pack(fill="x")
        ttk.Button(bar, text="⚙ Ayarlar", command=self._settings).pack(side="left", padx=3)
        ttk.Button(bar, text="🎙 4 sn Test", command=self._test).pack(side="left", padx=3)
        ttk.Button(bar, text="🚀 Otomatik Başlat", command=self._autostart).pack(side="left", padx=3)
        ttk.Button(bar, text="❌ Çıkış", command=self.app.quit).pack(side="right", padx=3)

        self._last_text = None
        self._hist_len = -1
        self._poll()

    def _copy(self):
        txt = self.text.get("1.0", "end").strip()
        if txt:
            self.root.clipboard_clear()
            self.root.clipboard_append(txt)

    def _repaste(self):
        txt = self.text.get("1.0", "end").strip()
        if txt:
            threading.Thread(target=self.app.injector.inject, args=(txt,), daemon=True).start()

    def _settings(self):
        SettingsDialog(self.root, self.app)

    def _test(self):
        def job():
            from .audio import Recorder, duration_seconds, encode_wav, peak
            from .formatting import build_prompt
            from .providers import create_transcriber

            cfg = self.app.cfg
            rec = Recorder(cfg.sample_rate, cfg.audio_device, max_seconds=9)
            self.app.status_text = "Test: 4 sn konuşun…"
            rec.start()
            import time

            time.sleep(4)
            pcm = rec.stop()
            try:
                if peak(pcm) < cfg.silence_peak:
                    self.app.status_text = "Test: sessizlik — mikrofonu kontrol edin"
                    return
                wav = encode_wav(pcm, cfg.sample_rate)
                t = create_transcriber(cfg).transcribe(wav, language=cfg.language, prompt=build_prompt(cfg.prompt, cfg.vocabulary))
                self.app.last_text = t
                self.app.status_text = f"Test OK: {t[:80]}"
            except Exception as exc:
                self.app.status_text = f"Test hatası: {exc}"

        threading.Thread(target=job, daemon=True).start()

    def _autostart(self):
        try:
            enabled, _p = autostart.status()
            if enabled:
                autostart.disable()
                messagebox.showinfo("Dikte+", "Otomatik başlatma kapatıldı.")
            else:
                p = autostart.enable()
                messagebox.showinfo("Dikte+", f"Otomatik başlatma açıldı:\n{p}")
        except Exception as exc:
            messagebox.showerror("Dikte+", str(exc))

    def _poll(self):
        try:
            st = self.app.state
            self.canvas_dot.itemconfig(self._dot, fill=DOT_COLOR.get(st, "#9aa0a6"))
            self.status_lbl.config(text=self.app.status_text[:90])
            self.sub_lbl.config(text=f"Kısayol: {self.app.cfg.hotkey}  •  Sağlayıcı: {self.app.cfg.provider}  •  Dil: {self.app.cfg.language or 'oto'}")
            if st == "recording":
                self.timer_lbl.config(text=f"● {self.app.elapsed():04.1f} sn", foreground="red")
                self.mic_btn.config(text=f"⏹  Durdur ({self.app.elapsed():04.1f} sn)")
            elif st == "transcribing":
                self.timer_lbl.config(text="⏳ …", foreground="orange")
                self.mic_btn.config(text="⏳  Yazıya dökülüyor…")
            else:
                self.timer_lbl.config(text="", foreground="black")
                self.mic_btn.config(text="🎤  Kaydı Başlat")
            try:
                self.level["value"] = int(max(0.0, min(1.0, self.app.level)) * 100)
            except Exception:
                pass
            if self.app.last_text != self._last_text:
                self._last_text = self.app.last_text
                self.text.delete("1.0", "end")
                if self._last_text:
                    self.text.insert("1.0", self._last_text)
            if len(self.app.history) != self._hist_len:
                self._hist_len = len(self.app.history)
                self.hist.delete(0, "end")
                for h in list(self.app.history)[:30]:
                    self.hist.insert("end", (h[:90] + "…") if len(h) > 90 else h)
        except Exception:
            pass
        try:
            self.root.after(100, self._poll)
        except Exception:
            pass


def run_gui(app, with_tray: bool = True) -> None:
    """Tk ana döngüsünü çalıştır; tray simgesini arka planda başlatır."""
    root = tk.Tk()
    app._ui_root = root
    try:
        from tkinter import ttk as _ttk

        try:
            _ttk.Style().theme_use("clam")
        except Exception:
            pass
    except Exception:
        pass
    win = MainWindow(root, app)

    overlay = None
    if getattr(app.cfg, "overlay_enabled", True):
        try:
            from .ui_overlay import Overlay

            overlay = Overlay(root, app, on_open_main=lambda: (root.deiconify(), root.lift()))
        except Exception as exc:
            app.log(f"mini gösterge açılamadı: {exc}")

    # Ayar değişince hap'ı aç/kapat (basit yoklama)
    def _overlay_sync():
        try:
            want = bool(app.cfg.overlay_enabled)
            if overlay is not None:
                is_hidden = str(overlay.win.state()) == "withdrawn"
                if want and is_hidden:
                    overlay.show()
                elif not want and not is_hidden:
                    overlay.hide()
        except Exception:
            pass
        try:
            root.after(1000, _overlay_sync)
        except Exception:
            pass

    try:
        root.after(1000, _overlay_sync)
    except Exception:
        pass

    icon = None
    if with_tray:
        try:
            from .tray import build_icon

            icon = build_icon(app)
            app._icon = icon
            threading.Thread(target=icon.run, daemon=True).start()
        except Exception as exc:
            app.log(f"tray başlatılamadı: {exc}")

    def on_close():
        # Kapat (X) => tepsiye küçült; gerçek çıkış Çıkış butonundan.
        if with_tray and (icon is not None):
            root.withdraw()
        else:
            app.quit()
            try:
                root.destroy()
            except Exception:
                pass

    root.protocol("WM_DELETE_WINDOW", on_close)
    try:
        root.mainloop()
    finally:
        try:
            if icon is not None:
                icon.stop()
        except Exception:
            pass
