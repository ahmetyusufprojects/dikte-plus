"""Global kısayol yakalama.

Eşleşme normalize edilmiş tuş-adı string'leri üzerinden yapılır; böylece çekirdek
mantık pynput'tan bağımsız ve ekransız/klavyesiz test edilebilir.
"""

from __future__ import annotations

_ALIASES = {
    "control": "ctrl",
    "option": "alt",
    "opt": "alt",
    "win": "cmd",
    "windows": "cmd",
    "super": "cmd",
    "command": "cmd",
    "meta": "cmd",
    "return": "enter",
    "esc": "escape",
    "spacebar": "space",
    "pgup": "page_up",
    "pgdn": "page_down",
}


def parse_hotkey(spec: str) -> frozenset[str]:
    parts = [p.strip() for p in spec.lower().split("+")]
    keys = {_ALIASES.get(p, p) for p in parts if p}
    if not keys:
        raise ValueError(f"geçersiz kısayol: {spec!r}")
    return frozenset(keys)


def key_names(key) -> set[str]:
    """Bir tuş olayının cevap verdiği tüm adlar (örn. ctrl_l -> {'ctrl_l', 'ctrl'})."""
    names: set[str] = set()
    name = getattr(key, "name", None)
    if name:
        names.add(name)
        for suffix in ("_l", "_r", "_gr"):
            if name.endswith(suffix):
                names.add(name[: -len(suffix)])
    char = getattr(key, "char", None)
    if char:
        if "\x01" <= char <= "\x1a":  # ctrl+harf kontrol karakteri olarak gelir
            names.add(chr(ord(char) + 96))
        else:
            names.add(char.lower())
    if not names:
        vk = getattr(key, "vk", None)
        if vk is not None and (0x30 <= vk <= 0x39 or 0x41 <= vk <= 0x5A):
            names.add(chr(vk).lower())
    return names


class HotkeyListener:
    """Kombo tamamen basıldığında on_activate çağırır.

    "hold" modunda kombo tuşlardan biri bırakılır bırakılmaz on_deactivate çalışır.
    OS tuş-tekrarı yeniden tetiklemez.
    """

    def __init__(self, hotkey: str, mode: str, on_activate, on_deactivate=None):
        self.target = parse_hotkey(hotkey)
        self.mode = mode
        self.on_activate = on_activate
        self.on_deactivate = on_deactivate
        self._pressed: set[str] = set()
        self._active = False
        self._listener = None

    def handle_press(self, key) -> None:
        self._pressed |= key_names(key)
        if not self._active and self.target <= self._pressed:
            self._active = True
            self.on_activate()

    def handle_release(self, key) -> None:
        self._pressed -= key_names(key)
        if self._active and not (self.target <= self._pressed):
            self._active = False
            if self.mode == "hold" and self.on_deactivate is not None:
                self.on_deactivate()

    def start(self) -> None:
        from pynput import keyboard

        self._listener = keyboard.Listener(on_press=self.handle_press, on_release=self.handle_release)
        self._listener.start()

    def stop(self) -> None:
        if self._listener is not None:
            self._listener.stop()
            self._listener = None
