"""Ekran üstünde her zaman görünen mini kayıt göstergesi (kompakt hap).

- Küçük (240x48), yarı saydam (varsayılan alpha 0.8, config'den ayarlanır),
  yumuşak renkler ve **yuvarlak köşeler** (chroma-key saydamlığıyla).
- Uzun durum yazısı kutuya sığmazsa **sağa-sola kayan yazı** (marquee) olur.
- Sürüklenebilir: basılı tutup sürükle. Kısa tık = başlat/durdur.
- Windows'ta WS_EX_NOACTIVATE ile odak çalmaz: metin kutusundaki imleç
  hap'a tıklayınca kaybolmaz, yapıştırma hedefi korunur.
- Çift tık / sağ tık = ana pencereyi aç.
"""

from __future__ import annotations

import tkinter as tk
import tkinter.font as tkfont

# Yumuşak, düşük doygunluklu renkler
COLORS = {
    "idle": {"bg": "#2b2f36", "dot": "#9aa0a6", "fg": "#d7dae0"},
    "recording": {"bg": "#4a2e2e", "dot": "#e07a7a", "fg": "#f5e6e6"},
    "transcribing": {"bg": "#47402a", "dot": "#d9b96a", "fg": "#f2ead6"},
}

W, H, RADIUS = 240, 48, 14
_CHROMA = "magenta"  # pencerenin görünmez rengi (köşeler)


def _round_rect(canvas: tk.Canvas, x1, y1, x2, y2, r, **kw):
    pts = [x1 + r, y1, x2 - r, y1, x2, y1, x2, y1 + r, x2, y2 - r,
           x2, y2, x2 - r, y2, x1 + r, y2, x1, y2, x1, y2 - r, x1, y1 + r, x1, y1]
    return canvas.create_polygon(pts, smooth=True, **kw)


class Overlay:
    def __init__(self, root: tk.Tk, app, on_open_main=None):
        self.app = app
        self.on_open_main = on_open_main
        self.win = tk.Toplevel(root)
        self.win.overrideredirect(True)
        self.win.attributes("-topmost", True)
        try:
            self.win.configure(bg=_CHROMA)
            self.win.attributes("-transparentcolor", _CHROMA)
        except Exception:
            pass
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

        self.font = tkfont.Font(family="Segoe UI", size=8)
        self.font_bold = tkfont.Font(family="Segoe UI", size=8, weight="bold")

        self.cv = tk.Canvas(self.win, width=W, height=H, bg=_CHROMA, highlightthickness=0, bd=0)
        self.cv.pack(fill="both", expand=True)

        self._press_xy = None
        self._win_xy = None
        self._moved = False
        self._click_pending = None
        # Kayan yazı durumu
        self._mq_text = ""
        self._mq_off = 0.0
        self._mq_dir = 1
        self._mq_pause = 0

        for w in (self.win, self.cv):
            w.bind("<ButtonPress-1>", self._drag_start)
            w.bind("<B1-Motion>", self._drag_move)
            w.bind("<ButtonRelease-1>", self._click_toggle)
            w.bind("<Double-Button-1>", self._open_main)
            w.bind("<Button-3>", self._open_main)
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
        self._moved = True
        if self.on_open_main:
            self.on_open_main()

    # --- odak çalmayı engelle (Windows) ---
    def _make_noactivate(self):
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
        self.repin()

    def hide(self):
        self.win.withdraw()

    def exists(self) -> bool:
        try:
            return bool(self.win.winfo_exists())
        except Exception:
            return False

    def alive(self) -> bool:
        """Pencere hâlâ yaşıyor ve görünür mü? (bekçi bunu yoklar)."""
        try:
            return self.exists() and str(self.win.state()) != "withdrawn"
        except Exception:
            return False

    def repin(self) -> None:
        """En-üste bayrağını işletim sistemine yeniden işlet (odak çalmadan).

        Windows'ta tam ekran uygulamalar, Uzak Masaüstü, uyku/uyanma veya
        Explorer yeniden başlaması en-üst sırasını bozabiliyor; overlay
        uygulamalarının standart çözümü bunu periyodik tekrarlamaktır.
        """
        try:
            import sys

            if sys.platform != "win32":
                return
            import ctypes

            hwnd = self.win.winfo_id()
            HWND_TOPMOST = -1
            SWP_NOMOVE, SWP_NOSIZE, SWP_NOACTIVATE = 0x0002, 0x0001, 0x0010
            ctypes.windll.user32.SetWindowPos(
                hwnd, HWND_TOPMOST, 0, 0, 0, 0, SWP_NOMOVE | SWP_NOSIZE | SWP_NOACTIVATE
            )
        except Exception:
            pass

    # --- çizim ---
    def _texts(self, state: str):
        secs = self.app.elapsed()
        if state == "recording":
            return "Kaydediliyor — tıkla durdur", f"{secs:04.1f}"
        if state == "transcribing":
            return "Yazıya dökülüyor…", ""
        return (self.app.status_text or "Hazır"), ""

    def update(self):
        try:
            state = self.app.state if self.app.state in COLORS else "idle"
            c = COLORS[state]
            cv = self.cv
            cv.delete("all")
            _round_rect(cv, 1, 1, W - 1, H - 1, RADIUS, fill=c["bg"], outline="")
            # Nokta
            cv.create_oval(12, 12, 22, 22, fill=c["dot"], outline="")
            # Süre (sağda sabit)
            status_txt, timer_txt = self._texts(state)
            if timer_txt:
                cv.create_text(W - 10, 17, text=timer_txt, anchor="e", font=self.font_bold, fill=c["fg"])
                max_w = W - 36 - self.font_bold.measure(timer_txt) - 10
            else:
                max_w = W - 36 - 8
            # Durum yazısı: sığmazsa kayan yazı
            tw = self.font.measure(status_txt)
            if tw <= max_w:
                self._mq_text, self._mq_off, self._mq_dir, self._mq_pause = status_txt, 0.0, 1, 0
                cv.create_text(28, 17, text=status_txt, anchor="w", font=self.font, fill=c["fg"])
            else:
                if status_txt != self._mq_text:
                    self._mq_text, self._mq_off, self._mq_dir, self._mq_pause = status_txt, 0.0, 1, 6
                span = tw - max_w
                if self._mq_pause > 0:
                    self._mq_pause -= 1
                else:
                    self._mq_off += 1.6 * self._mq_dir
                    if self._mq_off >= span:
                        self._mq_off, self._mq_dir, self._mq_pause = float(span), -1, 8
                    elif self._mq_off <= 0:
                        self._mq_off, self._mq_dir, self._mq_pause = 0.0, 1, 8
                cv.create_text(28 - self._mq_off, 17, text=status_txt, anchor="w", font=self.font, fill=c["fg"])
            # Ses seviyesi barı
            lvl = max(0.0, min(1.0, self.app.level)) if state == "recording" else 0.0
            cv.create_rectangle(14, H - 12, W - 14, H - 9, fill="#1d2025", outline="")
            if state == "recording" and lvl > 0.01:
                cv.create_rectangle(14, H - 12, 14 + int((W - 28) * lvl), H - 9, fill=c["dot"], outline="")
        except Exception:
            pass
        try:
            self.win.after(100, self.update)
        except Exception:
            pass


class OverlayWatchdog:
    """Hap bekçisi: 1 sn'de bir yoklar, hap ölmüş/gizlenmişse diriltir.

    Kapsadıkları:
    - pencere bir şekilde yok edildiyse -> sıfırdan yeniden oluşturur,
    - gizlenmişse (ama ayar açıksa) -> tekrar gösterir,
    - en-üst sırası bozulmuşsa -> ~5 sn'de bir yeniden iğneler (repin).
    Ayar kapalıysa hap'ı gizli tutar. Kendisi de Tk `after` ile yaşar.
    """

    def __init__(self, root: tk.Tk, app, on_open_main=None):
        self.root = root
        self.app = app
        self.on_open_main = on_open_main
        self.overlay: Overlay | None = None
        self._ticks = 0
        try:
            if bool(getattr(app.cfg, "overlay_enabled", True)):
                self.overlay = Overlay(root, app, on_open_main=on_open_main)
        except Exception as exc:
            try:
                app.log(f"mini gösterge açılamadı: {exc}")
            except Exception:
                pass
        try:
            root.after(1000, self.tick)
        except Exception:
            pass

    def tick(self):
        try:
            want = bool(getattr(self.app.cfg, "overlay_enabled", True))
            if not want:
                if self.overlay is not None and self.overlay.alive():
                    self.overlay.hide()
            else:
                if self.overlay is None or not self.overlay.exists():
                    try:
                        self.overlay = Overlay(self.root, self.app, on_open_main=self.on_open_main)
                        try:
                            self.app.log("mini hap yeniden oluşturuldu")
                        except Exception:
                            pass
                    except Exception:
                        self.overlay = None
                elif not self.overlay.alive():
                    self.overlay.show()
                if self.overlay is not None and self.overlay.alive():
                    self._ticks += 1
                    if self._ticks % 5 == 0:
                        self.overlay.repin()
        except Exception:
            pass
        try:
            self.root.after(1000, self.tick)
        except Exception:
            pass
