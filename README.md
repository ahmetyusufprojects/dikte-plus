# Dikte+ 🎤

**Groq Whisper tabanlı, görsel arayüzlü Türkçe sesli dikte uygulaması.**
Kısayola bas, konuş, bırak — metin imlecin neredeyse oraya yazılsın.

> `TypeLess` (`jlgadgeteer/typeless`, MIT) projesinden ilhamla sıfırdan yazıldı.
> TypeLess'in kanıtlanmış ses motoru aynen korundu, ama en büyük şikâyet çözüldü:
> **artık ne zaman kaydedip kaydetmediğini her an görüyorsun.**

| Durum | Görünüm |
|---|---|
| Hazır | Gri hap + `ctrl+shift+space` ipucu |
| Kaydediliyor | Kırmızı hap + canlı sayaç + ses seviyesi barı |
| Yazıya dökülüyor | Turuncu hap + "Yazıya dökülüyor…" |
| Bitti | Ana pencerede yeşil "✓ Yapıştırıldı (3,2 sn → 48 karakter)" + son metin kutusu |
| Hata | Kırmızı uyarı + sebep (örn. "API anahtarı reddedildi") |

Ek olarak tam boy **ana pencere** var: büyük 🎤 butonu, ses seviyesi, son metin,
geçmiş listesi, tek tıkla test, ayarlar penceresi ve tepsi simgesi.

## TypeLess nasıl çalışıyordu? (araştırma özeti)

Kullandığın orijinal uygulama (`pip install git+https://github.com/jlgadgeteer/typeless`,
v0.1.0, Python 3.10+) şu boru hattını kullanır — Dikte+ da aynısını kullanır:

```
kısayol (pynput) → mikrofon (sounddevice, 16 kHz mono int16)
  → WAV kodlama → Groq /audio/transcriptions (whisper-large-v3, ücretsiz katman)
  → isteğe bağlı LLM cilası (Llama 3.3, dolgu kelime temizliği)
  → kelime değişimleri + sondaki boşluk
  → panoya kopyala + Ctrl+V ile yapıştır + eski panoyu geri yükle
```

- **Durum bildirimi:** sadece tepsi simgesi rengi (gri / kırmızı / turuncu) + kısa bip sesleri.
  Konsol (`cmd`) dışında bir pencere yok — senin şikâyetin de tam buydu.
- **Kısayol modları:** `toggle` (bas-başlat / bas-durdur, varsayılan `ctrl+shift+space`)
  ve `hold` (basılı-tut, örn. `ctrl_r`).
- **Maliyet:** Groq ücretsiz katman; ücretlide ~0,11 $/saat ses. Ayda 1 saat konuşma
  1 $'ın çok altında. OpenAI alternatifi de desteklenir.
- **Doğruluk ayarları:** `vocabulary` (özel kelimeler), `replacements` (yanlış yazım düzeltme),
  `language` (örn. `tr` sabitleme), `cleanup:true` (AI cilası).

Kaynak: repo kökündeki `pyproject.toml`, `src/typeless/{app,audio,config,hotkey,inject,tray,sounds,providers}.py`
ve `README.md` tek tek okundu; `typeless-kaynak/` klasörüne klonlanıp incelendi.

## Özellikler

- ✅ Groq `whisper-large-v3` (ücretsiz) varsayılan; OpenAI / local faster-whisper / custom sunucu desteklenir
- ✅ Her zaman üstte mini hap: sayaç, VU-metre, tek tıkla başlat/durdur, sürüklenebilir
- ✅ Ana pencere: durum kartı, büyük mikrofon butonu, son metin + kopyala + tekrar-yapıştır, geçmiş (20)
- ✅ Ayarlar penceresi: sağlayıcı, API anahtarı, dil, kısayol, LLM cilası, bip, hap aç/kapat
- ✅ Türkçe tepsi menüsü: durum satırı, başlat/durdur, pencereyi aç, config'i aç, çıkış
- ✅ `typeless` config'ini otomatik taşır — API anahtarını yeniden girmezsin
- ✅ Sesli bildirimler (başlat/dur/bitti/hata) + görsel karşılıkları
- ✅ `dikte test`, `dikte devices`, `dikte transcribe dosya.wav`, `dikte autostart`

## Kurulum

Python 3.10+ gerekir (sende 3.11 var — uygun).

```powershell
# Bu repoyu klonla
git clone https://github.com/<kullanıcı-adın>/dikte-plus.git
cd dikte-plus

# Kur (düzenlenebilir kurulum önerilir)
pip install -e .

# Ücretsiz Groq anahtarı al (kredi kartı yok):
# https://console.groq.com/keys
dikte setup
#  - Sağlayıcı: groq
#  - API anahtarı: yapıştır
#  - Dil: tr
#  - Kısayol: ctrl+shift+space

# Mikrofonu dene
dikte test

# Başlat (ana pencere + mini hap + tepsi)
dikte
```

Komutlar:

| Komut | Ne yapar |
|---|---|
| `dikte` / `dikte gui` / `dikte run` | Görsel uygulamayı başlat |
| `dikte run --no-gui` | Eski tip konsol modu (TypeLess gibi) |
| `dikte run --no-tray` | Tepsisiz çalış |
| `dikte setup` | İnteraktif kurulum |
| `dikte test [sn]` | Kaydet + transkripti yazdır |
| `dikte devices` | Mikrofonları listele |
| `dikte transcribe ses.wav` | Dosyayı yazıya dök |
| `dikte config` / `dikte config set ANAHTAR DEĞER` | Ayarları gör/değiştir |
| `dikte autostart enable\|disable\|status` | Oturumda otomatik başlat |

## Kullanım

1. Herhangi bir metin kutusuna tıkla (Word, tarayıcı, WhatsApp…).
2. `Ctrl+Shift+Space`'e bas **veya** hap'a tıkla **veya** ana penceredeki 🎤 butonuna bas.
   - Hap kırmızı olur, sayaç işler, ses barı oynar → konuş.
3. Tekrar bas → hap turuncu olur ("Yazıya dökülüyor…", ~1 sn).
4. Metin imlece yapışır, ana pencerede son metin + geçmişe eklenir.

İpuçları:

```powershell
# Tek dilde dikte ediyorsan sabitle (doğruluk artar)
dikte config set language '"tr"'

# Özel isimler / jargon
dikte config set vocabulary '["PostHog", "Groq", "kubectl"]'

# Hâlâ yanlış yazılanlar için otomatik düzeltme
dikte config set replacements '{"post hog": "PostHog"}'

# Wispr Flow'daki sihir: dolgu kelime temizliği + kendi düzeltmelerin
dikte config set cleanup true

# Basılı-tut modu (Wispr Flow'a en yakın his)
dikte config set hotkey '"ctrl_r"'
dikte config set hotkey_mode '"hold"'

# Mini hap'ı kapat/aç
dikte config set overlay_enabled false
```

## Yapılandırma referansı

`dikte config` dosya yolunu ve içeriği yazdırır
(Windows: `%APPDATA%\dikte-plus\config.json`).

| Anahtar | Varsayılan | Not |
|---|---|---|
| `provider` | `groq` | `groq`, `openai`, `local`, `custom` |
| `model` | _(boş=varsayılan)_ | Groq'ta `whisper-large-v3` |
| `api_key` | _(boş)_ | Yoksa `GROQ_API_KEY` / `OPENAI_API_KEY` / `DIKTE_API_KEY` env |
| `base_url` | _(boş)_ | Sadece `custom` için |
| `language` | _(boş=oto)_ | Türkçe için `tr` önerilir |
| `prompt` / `vocabulary` | | Modele bağlam / kelime önyargısı |
| `replacements` | `{}` | Kelime-sınırı, büyük/küçük harf duyarsız |
| `hotkey` / `hotkey_mode` | `ctrl+shift+space` / `toggle` | `hold` = basılı-tut |
| `injection` | `paste` | `type` = karakter karakter yazma |
| `restore_clipboard` / `append_space` | `true` / `true` | Eski pano + sondaki boşluk |
| `cleanup` / `cleanup_provider` / `cleanup_model` | kapalı | LLM cilası |
| `sounds` | `true` | Bip sesleri |
| `audio_device` | sistem varsayılanı | `dikte devices` ile bak |
| `max_seconds` / `min_seconds` / `silence_peak` | `120` / `0.3` / `500` | Oto-dur / sessizlik filtresi |
| `overlay_enabled` / `overlay_position` / `history_size` | `true` / `top-center` / `20` | **Dikte+'ta yeni** |

## Sorun giderme

- **Hiçbir şey yazılmıyor** → başka uygulamaya yapıştırma engelleniyor olabilir;
  `dikte config set injection '"type"'` dene. Yönetici olarak çalışan uygulamaya
  dikte için Dikte+'yı da yönetici çalıştır.
- **Kısayol çalışmıyor** → başka uygulama aynı komboyu kapmış olabilir;
  `F8` veya `ctrl_r` gibi yan tuşlar en sorunsuzu. Değişiklikten sonra yeniden başlat.
- **"API anahtarı yok / reddedildi"** → `dikte setup` veya `GROQ_API_KEY` env.
  Anahtar: https://console.groq.com/keys
- **Yanlış mikrofon** → `dikte devices`, sonra `dikte config set audio_device 2`.
- **Kötü doğruluk** → `language tr` sabitle, `vocabulary` ekle, `whisper-large-v3`
  kullan (turbo değil), mikrofonu 15–30 cm tut.
- **Sessizlik atlandı** → giriş seviyesini yükselt, `silence_peak` düşür.

## Proje yapısı

```
src/dikte_plus/
  app.py         kayıt → transkripsiyon → yapıştırma çekirdeği + durum yayını
  ui_main.py     ana pencere + ayarlar + tray/GUI başlatıcı (tkinter)
  ui_overlay.py  her-zaman-üstte mini hap (sayaç + VU-metre)
  audio.py       mikrofon + WAV + ses seviyesi
  hotkey.py      global kısayol
  inject.py      panoyla yapıştırma
  tray.py        tepsi simgesi (Türkçe menü)
  sounds.py      bip tonları
  cleanup.py     LLM cilası
  formatting.py  değişim + boşluk + prompt
  config.py      JSON config (+ typeless'ten taşıma)
  autostart.py   oturumda başlat
  providers/     groq/openai/custom (HTTP) + local (faster-whisper)
  cli.py         `dikte` komutları
tests/           pytest birim testleri (donanım gerektirmez)
```

## Yol haritası

- [ ] Akışlı (streaming) transkripsiyon — konuşurken kısmi metin
- [ ] Sesli aktivite algılama — susunca oto-dur
- [ ] PyInstaller ile tek-dosya `.exe` (Python'suz kurulum)
- [ ] Uygulama-bazlı profil (e-posta vs. sohbet vs. kod yorumu tonu)

## Katkı / Lisans

MIT — `LICENSE` dosyasına bak. TypeLess'e teşekkürler (`jlgadgeteer/typeless`).

Öneri ve hata raporu için issue açın. PR'lar memnuniyetle karşılanır:
`ruff check .` + `pytest` temiz geçmeli.

---

### English summary

**Dikte+** is a visual, Turkish-first voice-dictation app for Windows/macOS powered by
Groq Whisper (free tier). Press `Ctrl+Shift+Space`, speak, and polished text is pasted
wherever your cursor is. Inspired by TypeLess (`jlgadgeteer/typeless`, MIT) — same proven
pipeline (hotkey → mic → STT → cleanup → paste) — but with an always-on-top recording
pill (timer + VU meter), a full main window (status, history, settings), and a Turkish
tray menu, so you always know whether you are recording. `pip install -e .`, get a free
key at https://console.groq.com/keys, run `dikte setup`, then `dikte`.
