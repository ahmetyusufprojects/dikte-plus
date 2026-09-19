# Dikte+ 🎤

> 🇹🇷 **Bu README önce Türkçe, sonra English olarak yazılmıştır.**
> 🇬🇧 **This README is written in Turkish first, then English.**

---

# 🇹🇷 TÜRKÇE

**Dikte+**, sesini yazıya çeviren ücretsiz bir dikte uygulamasıdır.
Kısayola basıp konuşursun, sözlerin imlecinin olduğu yere yazılır.
Altyapı olarak **Groq Whisper** kullanır — ücretsizdir, kredi kartı istemez.

## 5 Dakikada Kurulum (yeni başlayanlar için)

### 1. Python'u kur

- https://www.python.org/downloads/ adresinden **Python 3.10 veya üstünü** indir.
- ⚠️ Kurarken **"Add python.exe to PATH"** kutusunu işaretlemeyi unutma.
- Kontrol et (PowerShell'de):
  ```powershell
  python --version
  ```

### 2. Dikte+'ı indir ve kur

```powershell
git clone https://github.com/ahmetyusufprojects/dikte-plus.git
cd dikte-plus
pip install .
```

### 3. Ücretsiz Groq anahtarı al (2 dakika, kredi kartsız)

1. https://console.groq.com/keys adresine git, ücretsiz hesap aç.
2. **Create API Key** butonuna bas, anahtarı kopyala (`gsk_...` ile başlar).

### 4. Kurulumu tamamla

```powershell
dikte setup
```

Sana 4 soru sorar — hepsinde Enter'a basıp geçebilirsin, sonra düzenlersin:

| Soru | Önerilen cevap |
|---|---|
| Sağlayıcı | `groq` |
| API anahtarı | kopyaladığın `gsk_...` anahtarı |
| Kısayol | `ctrl+shift+space` |
| Dil | `tr` |

### 5. Mikrofonu dene

```powershell
dikte test
```

4 saniye konuş, yazıya dökülmüş halini ekranda gör. "Sessizlik" uyarısı alırsan
mikrofonunu kontrol et (`dikte devices` hangi mikrofonların bağlı olduğunu gösterir).

### 6. Başlat — bu kadar! 🎉

```powershell
dikte-gui
```

> `dikte` yazarsan terminal penceresi açık kalır (kapatırsan uygulama kapanır).
> Günlük kullanımda **`dikte-gui`** yaz — terminal açılmaz, yalnızca tepsi simgesi
> ve mini hap gelir. Ya da `scripts/DiktePlus-Sessiz.vbs` dosyasına çift tıkla.

Bilgisayar açılınca kendiliğinden başlasın istersen:

```powershell
dikte autostart enable
```

## Günlük Kullanım

1. Herhangi bir metin kutusuna tıkla (Word, tarayıcı, WhatsApp…).
2. `Ctrl+Shift+Space`'e bas **veya** ekrandaki mini hap'a tıkla.
   Hap kırmızı olur, süre sayar → konuş.
3. Bitince tekrar bas → hap turuncu olur ("Yazıya dökülüyor…", ~1 saniye).
4. Metin imlecin oraya yapışır. ✔

**İpucu:** Hap'a tıklamak yerine kısayolu kullan — faren metin kutusundan hiç
ayrılmaz, imleç hep doğru yerde kalır. (Hap odak çalmayacak şekilde tasarlandı,
ama kısayol her zaman en garantisidir.)

## Ses Temaları 🔊

Başlat/durdur sesleri artık tek frekanslı "bip" değil; araştırılıp seçilen
**yükselen ikili / alçalan ikili / üçlü zil** kalıplarında 4 hazır tema var:

| Tema | Karakter |
|---|---|
| `soft` (önerilen) | Yumuşak, E5→A5 yükselen |
| `bright` | Parlak, tiz ve hızlı |
| `calm` | Sakin, pes ve yavaş |
| `classic` | Eski tek-ton sesi |

```powershell
dikte sounds            # temaları listele
dikte sounds test soft  # dinle (başlat → durdur → bitti)
dikte sounds set calm   # seç
```

Ayarlar penceresinden de seçebilirsin (⚙ Ayarlar → Ses teması → ▶ Dene).

**Kendi sesini koymak istersen:** `start.wav`, `stop.wav`, `done.wav`,
`error.wav` dosyalarını config klasöründeki `sounds/` dizinine bırakman yeterli:

```powershell
dikte config   # en üstte config dosyasının yolunu yazar
# Örn: C:\Users\<sen>\AppData\Roaming\dikte-plus\sounds\start.wav
```

Ücretsiz (CC0) ses katalogları: https://sfxmint.com/category/ui ve
https://directory.audio/sound-effects/interface-ui

## Mini Hap 💊

- Her zaman en üstte, **yuvarlak köşeli**, yarı saydam küçük gösterge.
- Gri = hazır, kırmızı + sayaç = kaydediliyor, turuncu = yazıya dökülüyor.
- Basılı tutup **sürükleyebilirsin** (konum hatırlanmaz, her açılışta üst-ortada başlar).
- Uzun durum yazısı kutuya sığmazsa yazı **otomatik kayar** (sağa-sola marquee).
- Saydamlık: `dikte config set overlay_alpha 0.65` (0.4–1.0 arası).
- Kapatmak istersen: `dikte config set overlay_enabled false`.

## Komutlar

| Komut | Ne yapar |
|---|---|
| `dikte-gui` | Konsolsuz başlat (günlük kullanım) |
| `dikte` / `dikte gui` | Terminalli başlat |
| `dikte run --no-gui` | Penceresiz konsol modu |
| `dikte setup` | İnteraktif kurulum |
| `dikte test [sn]` | Kaydet, sonucu ekrana yaz |
| `dikte sounds [list\|test\|set]` | Ses temaları |
| `dikte devices` | Mikrofonları listele |
| `dikte transcribe ses.wav` | Ses dosyasını yazıya dök |
| `dikte config` / `dikte config set ANAHTAR DEĞER` | Ayarları gör/değiştir |
| `dikte autostart enable\|disable\|status` | Açılışta başlat |

## Sık Sorulan Sorular

- **Hiçbir şey yazılmıyor.** Yönetici olarak çalışan pencereye normal kullanıcı
  dikte edemez — Dikte+'ı yönetici çalıştır. Ya da `dikte config set injection '"type"'` dene.
- **Kısayol çalışmıyor.** Başka program aynı komboyu kapmış olabilir.
  `dikte config set hotkey '"f8"'` dene ve uygulamayı yeniden başlat.
- **"API anahtarı yok/reddedildi".** `dikte setup` ile anahtarı gir veya
  `GROQ_API_KEY` ortam değişkenini tanımla.
- **Kötü doğruluk.** `dikte config set language '"tr"'` ile dili sabitle,
  özel isimleri `vocabulary`'ye ekle, mikrofonu 15–30 cm tut.
- **`cleanup` nedir?** `dikte config set cleanup true` — "ıı, şey" gibi dolgu
  kelimelerini temizleyen, kendi düzeltmelerini uygulayan ("5 değil 6" → "6")
  ücretsiz yapay zekâ cilası.

## Katkı

Hata/öneri için issue aç, PR gönder. `pytest` ve `ruff check .` temiz geçmeli.
Lisans: MIT (`LICENSE`). TypeLess'e (`jlgadgeteer/typeless`) ilham için teşekkürler.

---

# 🇬🇧 ENGLISH

**Dikte+** is a free voice-dictation app: press a hotkey, speak, and your words are
typed wherever your cursor is. Powered by **Groq Whisper** — free tier, no credit card.

## 5-Minute Setup (beginners)

### 1. Install Python

- Download **Python 3.10+** from https://www.python.org/downloads/
- ⚠️ Check **"Add python.exe to PATH"** during install.
- Verify: `python --version`

### 2. Download & install Dikte+

```powershell
git clone https://github.com/ahmetyusufprojects/dikte-plus.git
cd dikte-plus
pip install .
```

### 3. Get a free Groq key (2 min, no credit card)

1. Sign up at https://console.groq.com/keys
2. Click **Create API Key**, copy it (starts with `gsk_...`).

### 4. Finish setup

```powershell
dikte setup
```

Suggested answers: provider `groq`, paste your key, hotkey `ctrl+shift+space`,
language `tr` (or `en`).

### 5. Test your mic

```powershell
dikte test
```

Speak for 4 seconds and read the transcript. If it says "silence", check your mic
(`dikte devices` lists them).

### 6. Launch — done! 🎉

```powershell
dikte-gui
```

> `dikte` keeps a terminal open (closing it quits the app).
> For daily use run **`dikte-gui`** — no terminal, just tray icon + mini pill.
> Or double-click `scripts/DiktePlus-Sessiz.vbs`.

Auto-start at login (no terminal window):

```powershell
dikte autostart enable
```

## Daily Use

1. Click any text field. 2. Press `Ctrl+Shift+Space` **or** click the mini pill.
   Red + timer = recording. 3. Press again → orange ("transcribing…", ~1s).
   4. Text is pasted at your cursor. ✔

**Tip:** prefer the hotkey over clicking the pill — your mouse never leaves the
text field. (The pill is focus-free by design, but the hotkey is bulletproof.)

## Sound Themes 🔊

Start/stop sounds are no longer plain beeps — 4 built-in themes with
ascending/descending chime patterns (researched from free UI catalogs):

| Theme | Character |
|---|---|
| `soft` (recommended) | Gentle, ascending E5→A5 |
| `bright` | Bright, high and fast |
| `calm` | Calm, low and slow |
| `classic` | Legacy single-tone |

```powershell
dikte sounds            # list themes
dikte sounds test soft  # preview (start → stop → done)
dikte sounds set calm   # select
```

Or pick from the Settings window (⚙ Settings → Sound theme → ▶ Preview).

**Custom sounds:** drop `start.wav`, `stop.wav`, `done.wav`, `error.wav` into the
`sounds/` folder next to your config (`dikte config` prints the path).
Free CC0 catalogs: https://sfxmint.com/category/ui,
https://directory.audio/sound-effects/interface-ui

## Mini Pill 💊

- Always-on-top, **rounded corners**, semi-transparent indicator.
- Gray = idle, red + timer = recording, orange = transcribing.
- **Draggable** (hold and drag). Long status text **auto-scrolls** (marquee).
- Transparency: `dikte config set overlay_alpha 0.65` (0.4–1.0).
- Disable: `dikte config set overlay_enabled false`.

## Commands

| Command | What it does |
|---|---|
| `dikte-gui` | Console-free launch (daily use) |
| `dikte` / `dikte gui` | Launch with terminal |
| `dikte setup` / `test` / `devices` / `transcribe` | Setup / mic test / devices / file |
| `dikte sounds [list\|test\|set]` | Sound themes |
| `dikte config` / `dikte config set KEY VALUE` | View/change settings |
| `dikte autostart enable\|disable\|status` | Start at login |

## FAQ

- **Nothing is typed.** Admin windows need an admin Dikte+. Or try
  `dikte config set injection '"type"'`.
- **Hotkey does nothing.** Another app may own the combo; try `f8` and restart.
- **API key missing/rejected.** Run `dikte setup` or set `GROQ_API_KEY`.
- **Poor accuracy.** Pin the language (`dikte config set language '"en"'`),
  add jargon to `vocabulary`, keep mic 15–30 cm away.

## Contributing

Issues and PRs welcome. `pytest` and `ruff check .` must pass. MIT (`LICENSE`).
Thanks to TypeLess (`jlgadgeteer/typeless`) for inspiration.
