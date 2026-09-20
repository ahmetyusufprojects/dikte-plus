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


@pytest.mark.skipif(sys.platform != "win32", reason="yalnızca Windows")
def test_enable_starts_minimized(tmp_path):
    """Açılış kaydı ana penceresiz başlamalı (yalnızca tepsi + hap)."""
    out = enable(startup_dir=tmp_path)
    content = open(out, encoding="utf-8").read()
    assert "--minimized" in content


def test_vbs_no_underscore_identifiers():
    """VBScript'te _ ile başlayan değişken yasak (800A0408 verir)."""
    import re

    from dikte_plus.autostart import _vbs_text, _win_target

    exe, args = _win_target()
    text = _vbs_text(exe, args, "pythonw -m dikte_plus run")
    assert not re.search(r"(?m)(?:^|\s)_[A-Za-z]", text)


@pytest.mark.skipif(sys.platform != "win32", reason="yalnızca Windows")
def test_vbs_compiles_with_cscript(tmp_path):
    """Üretilen VBS'yi Run satırları Echo'ya çevrilmiş halde cscript'ten geçir."""
    import re
    import subprocess

    from dikte_plus.autostart import _vbs_text, _win_target

    exe, args = _win_target()
    text = _vbs_text(exe, args, "pythonw -m dikte_plus run")
    checked = re.sub(r"(?m)^\s*\S+\.Run .*$", '  WScript.Echo "BRANCH_OK"', text)
    p = tmp_path / "check.vbs"
    p.write_text(checked, encoding="ascii")
    r = subprocess.run(["cscript", "//Nologo", str(p)], capture_output=True, text=True, timeout=30)
    assert r.returncode == 0, r.stderr
    assert "BRANCH_OK" in r.stdout
