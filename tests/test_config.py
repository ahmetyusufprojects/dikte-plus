from dikte_plus.config import Config, load_config, save_config, set_value


def test_defaults_groq():
    assert Config().provider == "groq"


def test_overlay_defaults():
    cfg = Config()
    assert cfg.overlay_enabled is True
    assert 0.4 <= cfg.overlay_alpha <= 1.0


def test_set_value_json():
    cfg = Config()
    set_value(cfg, "vocabulary", '["Groq"]')
    assert cfg.vocabulary == ["Groq"]


def test_save_load_roundtrip(tmp_path):
    cfg = Config(language="tr", hotkey="ctrl+shift+space")
    p = tmp_path / "config.json"
    save_config(cfg, p)
    back = load_config(p)
    assert back.language == "tr"
