from dikte_plus import sounds


def test_themes_listed():
    themes = sounds.list_themes()
    assert set(themes) == {"soft", "bright", "calm", "classic"}


def test_each_theme_builds_all_kinds():
    for theme in sounds.list_themes():
        for kind in ("start", "stop", "done", "error"):
            pcm = sounds._pcm(theme, kind)
            assert pcm and len(pcm) > 1000


def test_unknown_theme_falls_back_to_soft():
    assert sounds._pcm("nope", "start") == sounds._pcm("soft", "start")


def test_unknown_kind_returns_none():
    assert sounds._pcm("soft", "nope") is None
