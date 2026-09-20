import sys

import pytest

from dikte_plus.autostart import _vbs_text, enable


def test_vbs_quotes_path_with_spaces():
    """Kullanıcı adında boşluk varsa (80070002) diye yol üç tırnak içinde olmalı."""
    exe = r"C:\Users\Ahmet Yusuf AYDIN\AppData\Local\Programs\Python\Python311\Scripts\dikte-gui.exe"
    text = _vbs_text(exe, "", "pythonw -m dikte_plus run")
    assert f'"""{exe}"""' in text
    assert "FileExists" in text
    assert "pythonw -m dikte_plus run" in text


def test_vbs_args_outside_quotes():
    text = _vbs_text(r"C:\py\pythonw.exe", " -m dikte_plus run", "pythonw -m dikte_plus run")
    assert '"""C:\\py\\pythonw.exe""" -m dikte_plus run' in text


@pytest.mark.skipif(sys.platform != "win32", reason="yalnızca Windows")
def test_enable_writes_quoted_vbs(tmp_path):
    out = enable(startup_dir=tmp_path)
    content = open(out, encoding="utf-8").read()
    assert content.count('"""') >= 2
    assert "FileExists" in content
