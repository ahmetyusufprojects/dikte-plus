from dikte_plus.formatting import build_prompt, format_text


def test_format_strip_and_space():
    assert format_text(" merhaba ", {}, True) == "merhaba "


def test_format_replacements_case_insensitive():
    out = format_text("post hog harika", {"post hog": "PostHog"}, False)
    assert out == "PostHog harika"


def test_format_empty():
    assert format_text("   ", {}, True) == ""


def test_build_prompt():
    p = build_prompt("toplantı notu", ["Groq", "kubectl"])
    assert "toplantı" in p and "Groq" in p
