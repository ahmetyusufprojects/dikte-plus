from dikte_plus.audio import duration_seconds, encode_wav, peak


def test_peak_silence():
    assert peak(b"\x00\x00" * 100) == 0


def test_duration():
    assert duration_seconds(b"\x00\x00" * 16000, 16000) == 1.0


def test_encode_wav_header():
    wav = encode_wav(b"\x00\x00" * 100, 16000)
    assert wav[:4] == b"RIFF"
