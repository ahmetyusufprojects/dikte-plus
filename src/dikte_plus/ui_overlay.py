"""Ekran üstünde her zaman görünen mini kayıt göstergesi (kompakt hap).

- Küçük (230x46), yarı saydam (varsayılan alpha 0.8, config'den ayarlanır),
  yumuşak renkler; dikkat dağıtmaz.
- Sürüklenebilir: basılı tutup sürükle. Kısa tık = başlat/durdur.
- Windows'ta WS_EX_NOACTIVATE ile odak çalmaz: metin kutusundaki imleç
  hap'a tıklayınca kaybolmaz, yapıştırma hedefi korunur.
- Çift tık / sağ tık = ana pencereyi aç.
"""

from __future__ import annotations

import tkinter as tk

# Yumuşak, düşük doygunluklu renkler (eski canlı kırmızı/turuncu yerine)
COLORS = {
    "idle": {"bg": "#2b2f36", "dot": "#9aa0a6", "fg": "#d7dae0"},
    "recording": {"bg": "#4a2e2e", "dot": "#e07a7a", "fg": "#f5e6e6"},
    "transcribing": {"bg": "#47402a", "dot": "#d9b96a", "fg": "#f2ead6"},
}

W, H = 230, 46


class Overlay:
    def __init__(self, root: tk.Tk, app, on_open_main=None):
        self.app = app
        self.on_open_main = on_open_main
        self.win = tk.Toplevel(root)
        self.win.overrideredirect(True)
        self.win.attributes("-topmost", True)
        try:
            alpha = float(getattr(app.cfg, "overlay_alpha", 0.8) or 0.8)
            alpha = max(0.4, min(1.0, alpha))
        except Exception:
            alpha = 0.8
        try:
            self.win.attributes("-alpha", alpha)
        except Exception:
            pass
        self.win.geometry(f"{W}x{H}")
        self._place()
        self.win.update_idletasks()
        self._make_noactivate()

        self._press_xy = None
        self._win_xy = None
        self._moved = False

        self.frame = tk.Frame(self.win, bg=COLORS["idle"]["bg"])
        self.frame.pack(fill="both", expand=True)

        self.top = tk.Frame(self.frame, bg=COLORS["idle"]["bg"])
        self.top.pack(fill="x", padx=8, pady=(6, 0))
        self.dot = tk.Label(self.top, text="●", bg=COLORS["idle"]["bg"], fg=COLORS["idle"]["dot"], font=("Segoe UI", 8))
        self.dot.pack(side="left")
        self.status = tk.Label(
            self.top, text="Hazır", bg=COLORS["idle"]["bg"], fg=COLORS["idle"]["fg"], font=("Segoe UI", 8)
        )
        self.status.pack(side="left", padx=(5, 0))
        self.timer = tk.Label(self.top, text="", bg=COLORS["idle"]["bg"], fg=COLORS["idle"]["fg"], font=("Segoe UI", 8))
        self.timer.pack(side="right")

        self.bar = tk.Canvas(self.frame, height=4, bg=COLORS["idle"]["bg"], highlightthickness=0)
        self.bar.pack(fill="x", padx=8, pady=(4, 6))

        for w in (self.win, self.frame, self.top, self.dot, self.status, self.timer, self.bar):
            w.bind("<ButtonPress-1>", self._drag_start)
            w.bind("<B1-Motion>", self._drag_move)
            w.bind("<ButtonRelease-1>", self._click_toggle)
            w.bind("<Double-Button-1>", self._open_main)
            w.bind("<Button-3>", self._open_main)
        self._click_pending = None
        self.update()

    # --- konum / sürükleme ---
    def _place(self):
        try:
            sw = self.win.winfo_screenwidth()
            pos = getattr(self.app.cfg, "overlay_position", "top-center")
            if pos == "bottom-right":
                x = sw - W - 20
                y = self.win.winfo_screenheight() - H - 60
            else:
                x = (sw - W) // 2
                y = 16
            self.win.geometry(f"{W}x{H}+{x}+{y}")
        except Exception:
            pass

    def _drag_start(self, ev):
        self._press_xy = (ev.x_root, ev.y_root)
        self._win_xy = (self.win.winfo_x(), self.win.winfo_y())
        self._moved = False

    def _drag_move(self, ev):
        if self._press_xy is None:
            return
        dx = ev.x_root - self._press_xy[0]
        dy = ev.y_root - self._press_xy[1]
        if abs(dx) + abs(dy) > 4:
            self._moved = True
        if self._moved and self._win_xy is not None:
            self.win.geometry(f"+{self._win_xy[0] + dx}+{self._win_xy[1] + dy}")

    def _click_toggle(self, _ev):
        # Sürükleme ise toggle yapma; kısa tık ise başlat/durdur.
        # Çift tıkı beklemek için 220 ms gecikmeli çalış (yoksa çift tık 2x toggle yapar).
        moved, self._moved = self._moved, False
        self._press_xy = None
        if moved:
            return
        if self._click_pending is not None:
            try:
                self.win.after_cancel(self._click_pending)
            except Exception:
                pass
        self._click_pending = self.win.after(220, self._do_toggle)

    def _do_toggle(self):
        self._click_pending = None
        try:
            self.app.toggle()
        except Exception:
            pass

    def _open_main(self, _ev=None):
        if self._click_pending is not None:
            try:
                self.win.after_cancel(self._click_pending)
            except Exception:
                pass
            self._click_pending = None
        self._moved = True  # çift tıkın tek-tık toggle'ını iptal et
        if self.on_open_main:
            self.on_open_main()

    # --- odak çalmayı engelle (Windows) ---
    def _make_noactivate(self):
        """Hap'a tıklanınca önceki uygulamanın odağını çalma.

        Windows'ta WS_EX_NOACTIVATE + WS_EX_TOOLWINDOW bayrakları ayarlanır:
        hap tıklanabilir kalır ama etkin pencere değişmez, böylece metin
        kutusundaki imleç korunur ve yapıştırma doğru yere gider.
        """
        try:
            import sys

            if sys.platform != "win32":
                return
            import ctypes

            hwnd = self.win.winfo_id()
            GWL_EXSTYLE = -20
            WS_EX_NOACTIVATE = 0x08000000
            WS_EX_TOOLWINDOW = 0x00000080
            style = ctypes.windll.user32.GetWindowLongW(hwnd, GWL_EXSTYLE)
            ctypes.windll.user32.SetWindowLongW(hwnd, GWL_EXSTYLE, style | WS_EX_NOACTIVATE | WS_EX_TOOLWINDOW)
        except Exception:
            pass

    def show(self):
        self.win.deiconify()
        self.win.update_idletasks()
        self._make_noactivate()

    def hide(self):
        self.win.withdraw()

    def update(self):
        try:
            state = self.app.state if self.app.state in COLORS else "idle"
            c = COLORS[state]
            secs = self.app.elapsed()
            if state == "recording":
                status_txt = "Kaydediliyor — durdurmak için tıkla"
                timer_txt = f"{secs:04.1f}"
            elif state == "transcribing":
                status_txt = "Yazıya dökülüyor…"
                timer_txt = ""
            else:
                status_txt = (self.app.status_text or "Hazır")[:30]
                timer_txt = ""
            for w in (self.frame, self.top):
                w.configure(bg=c["bg"])
            for w in (self.dot, self.status, self.timer):
                w.configure(bg=c["bg"])
            self.dot.configure(fg=c["dot"])
            self.status.configure(text=status_txt, fg=c["fg"])
            self.timer.configure(text=timer_txt, fg=c["fg"])
            self.bar.configure(bg=c["bg"])
            self.bar.delete("all")
            w = self.bar.winfo_width() or (W - 16)
            lvl = max(0.0, min(1.0, self.app.level))
            if state == "recording":
                self.bar.create_rectangle(0, 0, int(w * lvl), 4, fill=c["dot"], outline="")
            else:
                self.bar.create_rectangle(0, 0, w, 1, fill="#454b54", outline="")
        except Exception:
            pass
        try:
            self.win.after(100, self.update)
        except Exception:
            pass
