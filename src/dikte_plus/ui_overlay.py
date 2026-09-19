"""Ekran üstünde her zaman görünen mini kayıt göstergesi (Wispr Flow tarzı hap).

TypeLess'teki en büyük eksik buydu: kullanıcı cmd penceresine bakmadan
kaydın başlayıp başlamadığını anlayamıyordu. Bu hap:
- her zaman en üstte, sürüklenebilir,
- idle = gri, recording = kırmızı + sayaç + ses barı, transcribing = turuncu,
- tek tık = başlat/durdur, sağ tık / çift tık = ana pencereyi aç.
"""

from __future__ import annotations

import tkinter as tk

COLORS = {
    "idle": {"bg": "#23262d", "dot": "#9aa0a6", "fg": "#e8eaed"},
    "recording": {"bg": "#5a1f1f", "dot": "#ff5252", "fg": "#ffffff"},
    "transcribing": {"bg": "#5a4413", "dot": "#ffb74d", "fg": "#ffffff"},
}

DOT = {"idle": "⚪", "recording": "🔴", "transcribing": "🟠"}


class Overlay:
    def __init__(self, root: tk.Tk, app, on_open_main=None):
        self.app = app
        self.on_open_main = on_open_main
        self.win = tk.Toplevel(root)
        self.win.overrideredirect(True)
        self.win.attributes("-topmost", True)
        try:
            self.win.attributes("-alpha", 0.94)
        except Exception:
            pass
        self.win.geometry("340x72")
        self._place()
        self._drag = None

        self.frame = tk.Frame(self.win, bg=COLORS["idle"]["bg"])
        self.frame.pack(fill="both", expand=True)
        for w in (self.win, self.frame):
            w.bind("<ButtonPress-1>", self._drag_start)
            w.bind("<B1-Motion>", self._drag_move)
            w.bind("<Button-1>", self._click_toggle)
            w.bind("<Double-Button-1>", self._open_main)
            w.bind("<Button-3>", self._open_main)

        self.top = tk.Frame(self.frame, bg=COLORS["idle"]["bg"])
        self.top.pack(fill="x", padx=10, pady=(8, 0))
        self.dot = tk.Label(self.top, text="⚪", bg=COLORS["idle"]["bg"], fg="white", font=("Segoe UI", 11))
        self.dot.pack(side="left")
        self.status = tk.Label(
            self.top, text="Dikte+ Hazır", bg=COLORS["idle"]["bg"], fg="white", font=("Segoe UI", 10, "bold")
        )
        self.status.pack(side="left", padx=(6, 0))
        self.timer = tk.Label(self.top, text="", bg=COLORS["idle"]["bg"], fg="white", font=("Segoe UI", 10))
        self.timer.pack(side="right")
        for w in (self.top, self.dot, self.status, self.timer):
            w.bind("<ButtonPress-1>", self._drag_start)
            w.bind("<B1-Motion>", self._drag_move)
            w.bind("<Button-1>", self._click_toggle)
            w.bind("<Double-Button-1>", self._open_main)
            w.bind("<Button-3>", self._open_main)

        self.bar = tk.Canvas(self.frame, height=8, bg=COLORS["idle"]["bg"], highlightthickness=0)
        self.bar.pack(fill="x", padx=10, pady=(6, 10))
        self._click_pending = None
        self.update()

    def _place(self):
        try:
            sw = self.win.winfo_screenwidth()
            pos = getattr(self.app.cfg, "overlay_position", "top-center")
            if pos == "bottom-right":
                x = sw - 360
                y = self.win.winfo_screenheight() - 120
            else:
                x = (sw - 340) // 2
                y = 24
            self.win.geometry(f"340x72+{x}+{y}")
        except Exception:
            pass

    def _drag_start(self, ev):
        self._drag = (ev.x_root - self.win.winfo_x(), ev.y_root - self.win.winfo_y())

    def _drag_move(self, ev):
        if self._drag:
            self.win.geometry(f"+{ev.x_root - self._drag[0]}+{ev.y_root - self._drag[1]}")

    def _click_toggle(self, _ev):
        # Sürükleme ile tek tıkı ayırt et: 180 ms içinde hareket yoksa toggle.
        if self._click_pending is not None:
            try:
                self.win.after_cancel(self._click_pending)
            except Exception:
                pass
        self._click_pending = self.win.after(180, self.app.toggle)

    def _open_main(self, _ev=None):
        if self._click_pending is not None:
            try:
                self.win.after_cancel(self._click_pending)
            except Exception:
                pass
            self._click_pending = None
        if self.on_open_main:
            self.on_open_main()

    def show(self):
        self.win.deiconify()

    def hide(self):
        self.win.withdraw()

    def update(self):
        try:
            state = self.app.state if self.app.state in COLORS else "idle"
            c = COLORS[state]
            secs = self.app.elapsed()
            if state == "recording":
                status_txt = f"KAYDEDİLİYOR  {secs:04.1f} sn — durdurmak için tıkla"
                timer_txt = ""
            elif state == "transcribing":
                status_txt = "Yazıya dökülüyor…"
                timer_txt = ""
            else:
                short = (self.app.status_text or "Hazır")[:42]
                status_txt = short
                timer_txt = f"{self.app.cfg.hotkey}"
            for w, bg in ((self.frame, c["bg"]), (self.top, c["bg"])):
                w.configure(bg=bg)
            for w in (self.dot, self.status, self.timer):
                w.configure(bg=c["bg"], fg=c["fg"])
            self.dot.configure(text=DOT.get(state, "⚪"))
            self.status.configure(text=status_txt)
            self.timer.configure(text=timer_txt)
            self.bar.configure(bg=c["bg"])
            self.bar.delete("all")
            w = self.bar.winfo_width() or 300
            lvl = max(0.0, min(1.0, self.app.level))
            fill = c["dot"] if state == "recording" else "#3a3f47"
            if state == "recording":
                self.bar.create_rectangle(0, 0, int(w * lvl), 8, fill=fill, outline="")
            else:
                self.bar.create_rectangle(0, 0, w, 2, fill=fill, outline="")
        except Exception:
            pass
        try:
            self.win.after(100, self.update)
        except Exception:
            pass
