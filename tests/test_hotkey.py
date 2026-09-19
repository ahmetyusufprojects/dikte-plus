from dikte_plus.hotkey import HotkeyListener, parse_hotkey


def test_parse():
    assert parse_hotkey("ctrl+shift+space") == frozenset({"ctrl", "shift", "space"})


def test_toggle_flow():
    calls = []
    hl = HotkeyListener("ctrl+shift+space", "toggle", lambda: calls.append("on"), lambda: calls.append("off"))

    class K:
        def __init__(self, name=None, char=None):
            self.name = name
            self.char = char

    hl.handle_press(K(name="ctrl_l"))
    hl.handle_press(K(name="shift"))
    hl.handle_press(K(name="space"))
    assert calls == ["on"]
    hl.handle_release(K(name="shift"))
    assert calls == ["on"]  # toggle modunda bırakınca off yok
