# SPHEREview — Yol Haritası

**NASA Space Apps Challenge 2026 · Challenge: "Planet X and SPHEREx"**
Hazırlanma: 14 Kasım 2026 · Hackathon: 14–15 Kasım 2026 (48 saat)
Çalışma adı: *SPHEREview* (değiştirilebilir)

---

## 1. Görev özeti

| | |
|---|---|
| **Challenge** | Planet X and SPHEREx (Zorluk: Advanced · Astrophysics, Planets & Moons, Software) |
| **Ana hedef** | Herkese açık bir web aracı. Kullanıcı bir gökyüzü parçasının koordinatını (RA/Dec) girer. Araç o bölgenin SPHEREx görüntülerini küçük bir video gibi art arda oynatır ve hareket eden cisimler kolayca fark edilir. |
| **Zorunlu test hedefleri** | Barnard's Star · Epsilon Indi B (yıldız yörüngesindeki kahverengi cüce çifti) · WISE 0855−0714 (RA 08h55m10.831s, Dec −07°14′42.53″) · RW Aurigae ve R Draconis (değişen yıldızlar) |
| **Model / ilham** | WiseView (WISE/unWISE için blink aracı; Backyard Worlds gönüllüleri bununla yüzlerce keşif yaptı) |
| **Zorunlu katalog sürümü** | Gaia **DR3** (MAST). Not: Gaia DR4, 2 Aralık 2026'da yani hackathon'dan sonra çıkacak. Challenge açıkça DR3 istiyor. |

### "Potential considerations" maddelerinin özelliklere eşlenmesi

| Challenge önerisi | Bizim çözümümüz | Faz |
|---|---|---|
| Yeni veri sürümleri hızla geliyor, kolay güncellenebilsin | `config/releases.yaml` + TAP ile otomatik sürüm keşfi | 2 |
| 102 bandı yaratıcı biçimde göster; her dedektörün verisini topla | Epoch × dedektör bazlı coadd (D1…D6), "tüm bantlar" ve RGB sahte renk | 2, 4 |
| **Ekstra puan:** anında spektrum | Tıklanan noktada pozlama bazlı 0.75–5 µm spektrum | 4 |
| Farklı zamanlardaki görüntüleri topla/çıkar | Blink, Fark (epoch − referans) ve Toplam modları | 4 |
| Görüş alanını kullanıcı seçsin | FOV kaydırıcısı (1′–15′) + veri boyutu uyarısı | 2, 3 |
| Gaia / WISE overlay | Gaia DR3 (konumlar her karenin tarihine taşınır) + CatWISE/AllWISE | 3, 4 |
| URL ile sorgulanabilsin, gömülebilsin | Tüm durum URL parametrelerinde + `/embed` görünümü | 3 |
| Kontaminasyon bayrakları gibi metadata | FLAGS maske katmanı + kare bilgi paneli | 4 |
| Astropy, Aladin (CDS) gibi araçlar | Backend'de astropy/astroquery/reproject, frontend'de Aladin Lite v3 | 2, 4 |

---

## 2. Veri kaynakları (14.11.2026 itibarıyla doğrulandı)

### 2.1 SPHEREx (IRSA)

**Kullanılacak sürümler: DR1 + QR3 birlikte**
- **DR1** (Kasım 2026): Survey 1–2, QR3 pipeline'ıyla yeniden işlenmiş. All-Sky Spectral Cube de bu sürümle geldi.
- **QR3** (Eylül 2026'dan beri haftalık): Survey 3–4.
- QR2 eskidi ve SIA'da yok. QR1 kaldırıldı. **Bunları kullanmayacağız.**
- SIA2 koleksiyonları: `spherex_dr1`, `spherex_dr1_deep`, `spherex_qr3`, `spherex_qr3_deep`, `spherex_dr1_cube`

**Görüntü keşfi: TAP (önerilen; SIA'daki yaklaşık 1 günlük gecikme TAP'ta yok)**
```sql
-- https://irsa.ipac.caltech.edu/TAP
SELECT a.uri, p.planeid, p.time_bounds_lower, p.time_bounds_upper,
       p.energy_bandpassname, p.provenance_version
FROM spherex.artifact a JOIN spherex.plane p ON a.planeid = p.planeid
WHERE 1 = CONTAINS(POINT('ICRS', {ra}, {dec}), p.poly)
ORDER BY p.time_bounds_lower
-- dedektör filtresi: AND p.energy_bandpassname = 'SPHEREx-D2'
```

> ⚠️ `spherex.obscore.access_url` dosyaya değil bir DataLink belgesine gidiyor. Bu yüzden yukarıdaki plane + artifact birleştirmesi kullanılıyor.

**Görüntü indirme: Faz 1'de karar verildi** (ayrıntılar: [docs/spike_report.md](docs/spike_report.md))
- ✅ **Seçilen:** kendi HTTP Range okuyucumuz ile S3 HTTPS (`https://nasa-irsa-spherex.s3.us-east-1.amazonaws.com/<dr1|qr3>/...`). Sadece IMAGE satırları ve RICE sıkıştırılmış FLAGS satırları okunuyor: görüntü başına ~0.5 MB, seri 0.8 sn, 12 paralel görüntü 7.5 sn. Kod: `spikes/range_reader.py`.
- Yedek 1: aynı okuyucu, IRSA HTTPS üzerinden.
- Yedek 2: IRSA cutout servisi (`?center={ra},{dec}d&size={derece}`). Görüntü başına ~2 MB (EPSF kırpılmıyor) ve 14.11'de 503 verdi.
- ❌ Elenen: astropy + fsspec `.section`, görüntü başına ~10 sn.

**Level 2 spektral görüntü (MEF) yapısı**
- 2040×2040 px, **6.15″/px**, dosya başına yaklaşık 70 MB, her pointing'de 6 dedektör.
- HDU'lar: `IMAGE` (MJy/sr, **zodi çıkarılmamış**) · `FLAGS` (bitmask; bit adları `MSKNnnnn`, açıklamaları `MSKDnnnn` header'ında) · `VARIANCE` · `ZODI` (model) · `EPSF` (21×21 bölge, her biri 33×33 px, 5× oversample) · `WCS-WAVE` (dalga boyu tablosu)
- Konumsal WCS: `WCS(hdul["IMAGE"].header)` (TAN-SIP)
- Dalga boyu: `w = WCS(header, fobj=hdul, key="W"); w.sip = None; wl, bw = w.pixel_to_world(x, y)`

| Dedektör | Dalga boyu (µm) | R |
|---|---|---|
| D1 | 0.75–1.09 | 39 |
| D2 | 1.10–1.62 | 41 |
| D3 | 1.63–2.41 | 41 |
| D4 | 2.42–3.82 | 35 |
| D5 | 3.83–4.41 | 112 |
| D6 | 4.42–5.00 | 128 |

**Gözlem mantığı (tasarımı doğrudan etkiliyor)**
- 102 kanal = 6 dedektör × 17. SPHEREx bir lineer değişken filtre (LVF) kullanıyor: dalga boyu dedektör üzerinde konuma göre değişiyor. Yani **her pozlamada bir kaynak tek bir dalga boyunda ölçülür.** Ardışık pozlamalar aynı kaynağın farklı dalga boylarını tamamlar.
- Tüm gökyüzü yaklaşık **6 ayda bir** taranıyor. DR1 ile QR3 birlikte yaklaşık 4 survey eder; zaman tabanı 2025 baharından 2026 yazına, yaklaşık 1.2–1.5 yıl.
- Ekliptik kutuplarındaki derin alanlar (NEP/SEP, toplam yaklaşık 200 deg²) çok daha sık gözleniyor.
- Bir survey içinde aynı noktanın pozlamaları saatler ile günler arasına yayılıyor. Asteroitler bu pozlamalar arasında belirgin şekilde yer değiştirir.

**Diğer**
- HiPS küp (yalnızca görselleştirme, sabit stretch 0–40 MJy/sr): `https://irsa.ipac.caltech.edu/data/hips/SPHEREx/spherex_allsky_cube`
- Dalga boyu katmanı: `frame = 17*(band-1) + (kanal-1)`; 50 ve 51 numaralı kareler boş.
- **Zorunlu teşekkür metni** (README ve uygulama içine): *"This publication makes use of data products from the Spectro-Photometer for the History of the Universe, Epoch of Reionization and Ices Explorer (SPHEREx), which is a joint project of the Jet Propulsion Laboratory and the California Institute of Technology, and is funded by the National Aeronautics and Space Administration."*
- DOI'ler: DR1 görüntüleri 10.26131/IRSA678 · DR1 küp 10.26131/IRSA679 · QR3 10.26131/IRSA662

### 2.2 Gaia DR3 (MAST)
- MAST API servisi: `Mast.Catalogs.GaiaDR3.Cone` (parametreler: `ra`, `dec`, `radius`, hepsi derece). Uç nokta: `https://mast.stsci.edu/api/v0/invoke`
- ✅ Faz 1'de doğrulandı: tam DR3, 153 sütun (`source_id, ra, dec, pmra, pmdec, parallax, phot_g_mean_mag, ref_epoch` …), 3–12 sn. Barnard konumu 2026'ya taşındığında SIMBAD'la fark 0.001″.
- ⚠️ astroquery `Catalogs.query_region(..., catalog="Gaia", version=3)` **sessizce DR2'ye düşüyor. Kullanılmayacak.**
- Yedek kaynaklar (MAST çalışmazsa): ESA Gaia Archive TAP (`gaiadr3.gaia_source`) veya VizieR `I/355/gaiadr3`
- **Konumu gözlem tarihine taşıma** (DR3 referans epoch'u J2016.0 = MJD 57388.5; Gaia'nın `pmra` değeri zaten cos δ içeriyor):
  ```python
  dt = (t_obs_mjd - 57388.5) / 365.25
  ra_t  = ra  + pmra  / 3.6e6 * dt / cos(radians(dec))
  dec_t = dec + pmdec / 3.6e6 * dt
  ```
  Paralaks 6″'lik pikselin yanında ihmal edilebilir (en fazla yaklaşık 0.77″).
- Katalog katmanı adaptör olarak yazılacak. DR4 çıktığında tek satırla geçilebilecek.

### 2.3 Opsiyonel
- **WISE overlay:** IRSA TAP'ta CatWISE2020 ve AllWISE. Tablo adları Faz 4'te doğrulanacak.
- **İsim çözümleme:** CDS Sesame (`https://cds.unistra.fr/cgi-bin/nph-sesame/-oxp/SNV?<isim>`). SIMBAD verisini PM ve paralaksla döndürüyor. astroquery SIMBAD (TAP) 14.11'de 404 verdi. Yedek olarak 5 test hedefi gömülü listede tutulacak.
- **Bilinen asteroitler:** IMCCE SkyBoT veya JPL. "Bu hareketli cisim bilinen bir asteroit mi?" kontrolü için.

---

## 3. WiseView'dan çıkarılan dersler

- **Akış:** Koordinatı gir, blink anında başlasın. Tüm durum URL'de: `ra, dec, size, band, speed, trimbright, linear, color, mode, zoom`
- **Stretch:** asinh (`linear` parametresi asinh "a" değeri; 1 = tamamen lineer) ve tavan modu `fixed`, `percent` veya `adapt`
- **Karşılaştırma paneli:** WiseView altta statik bir PS1 görüntüsü gösteriyor. Biz bunun yerine Aladin Lite kullanacağız (2MASS/WISE/PS1/DSS HiPS + Gaia).
- **Gaia overlay:** Gönüllüler bilinen yıldızları ayıklamak için kullanıyor.
- **Bizim farkımız:**
  - 102 bant var. Dedektör bazlı renk, spektrum ve "molekül filtreleri" ekleyebiliriz.
  - Stretch tarayıcıda yapılır, yani kaydırıcılar anında tepki verir.
  - Gaia konumları her kareye taşınır, daire yıldızla birlikte hareket eder.

---

## 4. Fizibilite: test hedefleri SPHEREx'te ne kadar hareket eder?

Piksel 6.15″, zaman tabanı yaklaşık 1.2–1.5 yıl.

| Hedef | Tür | Öz hareket (yaklaşık) | Beklenen kayma | Ne göstereceğiz |
|---|---|---|---|---|
| Barnard's Star | Yakın M cücesi | ~10.4″/yıl | ~13–15″ ≈ **2+ px**, net | Blink'te açık hareket, Gaia dairesi yıldızı takip eder. Parlak olduğu için doygunluk bayraklarına dikkat. |
| WISE 0855−0714 | En soğuk kahverengi cüce | ~8.1″/yıl | ~10–12″ ≈ **~2 px** | Gaia'da yok (çok soğuk). D1'de görünmez, D5/D6'da parlak. "Gaia'da olmayan hareketli kırmızı kaynak" örneği, spektrum ile. |
| Epsilon Indi B | Kahverengi cüce çifti | ~4.7″/yıl | ~6–7″ ≈ **~1 px**, sınırda | Fark modunda dipol (artı/eksi) deseni. Yaklaşık 6.7′ ötedeki parlak Eps Indi A hayalet/hale üretebilir. |
| RW Aurigae | Genç, değişken yıldız | — | Konum değil, parlaklık değişir | Epoch blink + ışık eğrisi |
| R Draconis | Mira değişeni (~245 gün) | — | Parlaklık değişir | Epoch blink + ışık eğrisi + spektrum değişimi |

> ⚠️ **Koordinat epoch'u tuzağı (Faz 1'de doğrulandı):**
> - Barnard's Star 2000'den bu yana 4.5′ kaydı.
> - Challenge'ın WISE 0855 koordinatı yaklaşık 2010.45 epoch'una ait; 2026'da cisim o noktanın **~2.1′ batısında**.
>
> → Varsayılan FOV **5′** olacak. İsimle aramada konum gözlem tarihine taşınacak. Koordinat girildiğinde yakındaki yüksek öz hareketli bilinen cisimler için uyarı gösterilecek.
>
> **Ölçülen gerçek değerler** (Faz 1): Barnard 1.9 px / 1.10 yıl, Eps Ind B 1.1 px / 1.44 yıl, WISE 0855 1.4 px / 1.02 yıl. R Dra derin alanda (2493 görüntü).

---

## 5. Mimari

```
┌──────────────────── Tarayıcı (HTML/CSS/JS, build adımı yok) ─────────────────────┐
│  Kontroller + URL durumu  │  Canvas blink oynatıcı  │  Aladin Lite v3  │ Plotly  │
│  (RA/Dec, FOV, bant, mod) │  (stretch/colormap JS'te)│  (bağlam paneli) │ spektrum│
└──────────────▲───────────────────────────────────────────────────────────────────┘
               │ JSON (+ base64 float32 kareler, kare başı ~15 KB)
┌──────────────┴──────────── FastAPI backend (Python 3.12) ─────────────────────────┐
│ query.py (TAP) → fetch.py (paralel, retry, cache) → coadd.py (reproject + zodi +   │
│ flag maskesi + 1/σ² ağırlıklı ortalama) → spectrum.py / lightcurve.py              │
│ catalogs/: gaia.py (MAST DR3) · wise.py · simbad.py · skybot.py   │ diskcache     │
└──────▲───────────────────▲──────────────────▲──────────────────────▲──────────────┘
   IRSA TAP          IRSA cutout / S3      MAST (Gaia DR3)        SIMBAD
```

### Ana kararlar ve gerekçeleri
1. **Python backend.** FITS, WCS, reproject ve astroquery tarayıcıda pratik değil. Notebook'lardaki kod kalıpları doğrudan kullanılabilir.
2. **Build adımı olmayan frontend.** Node kurulu değil ve 48 saatte hız önemli. Aladin Lite ve Plotly CDN'den gelecek.
3. **Ham float32 kare gönderimi.** 60×60 piksellik bir kare yaklaşık 14 KB. Stretch, colormap ve invert tarayıcıda yapılır, kaydırıcılar sunucuya gitmeden anında çalışır. WiseView sunucuda render ettiği için daha yavaş.
4. **Coadd stratejisi:** her (epoch, dedektör) için:
   - tüm pozlamalar hedef merkezli ortak bir TAN ızgarasına reproject edilir,
   - `IMAGE − ZODI` alınır,
   - kötü FLAGS pikselleri maskelenir,
   - 1/VARIANCE ağırlıklı ortalama alınır.
   Challenge'ın önerdiği yaklaşım bu.
5. **Epoch tanımı:** pozlamalar zaman boşluklarına göre kümelenir (30 günden büyük boşluk yeni epoch başlatır, pratikte Survey 1…4 olur). Ayrıca "tek pozlama" modu: asteroitler gün içinde hareket eder.
6. **Güncellenebilirlik:** sürüm/koleksiyon listesi `config/releases.yaml` dosyasında. Yeni sürüm gelince tek satır eklenir. TAP `provenance_version` ile otomatik kontrol edilir.
7. **Önbellek:** cutout'lar `(dosya, merkez, boyut)` anahtarıyla diske, coadd sonuçları da ayrıca önbelleğe alınır. Demo öncesinde 5 test hedefi önceden yüklenir.

### API taslağı

| Uç nokta | Görev |
|---|---|
| `GET /api/resolve?name=` | SIMBAD ile isim çözer, PM ile konumu gözlem tarihine taşır |
| `GET /api/observations?ra&dec&fov` | Pozlama listesi: zaman, dedektör, sürüm, epoch grubu |
| `GET /api/frames?ra&dec&fov&mode=epoch\|exposure&det=1..6\|all` | Coadd kareleri (float32 base64 + WCS + metadata). Kademeli yükleme için SSE. |
| `GET /api/spectrum?ra&dec[&epoch]` | Pozlama bazlı fotometri: λ, akı, hata, bayrak |
| `GET /api/lightcurve?ra&dec&det` | Zaman–akı eğrisi |
| `GET /api/gaia?ra&dec&radius&epochs=` | Gaia DR3 kaynakları + her epoch için taşınmış konumlar |
| `GET /api/wise?ra&dec&radius` | CatWISE/AllWISE kaynakları |
| `GET /api/export/gif?...` | Blink'in GIF olarak dışa aktarımı |

### URL şeması (paylaşım ve gömme için)
```
/?ra=133.795&dec=-7.245&fov=5&det=6&mode=epoch&speed=500
  &stretch=asinh&a=0.1&pmin=1&pmax=99.5&cmap=gray&invert=0&zoom=8&gaia=1&wise=0
/embed?...   ← kontroller gizli, sadece oynatıcı (iframe için)
```

### Klasör yapısı
```
NASA_Space_Apps/
├─ ROADMAP.md · README.md · requirements.txt · .gitignore
├─ config/releases.yaml
├─ backend/
│  ├─ app.py                 # FastAPI, statik frontend'i de sunar
│  ├─ spherex/  query.py · fetch.py · epochs.py · coadd.py · spectrum.py · flags.py
│  ├─ catalogs/ gaia.py · wise.py · simbad.py · skybot.py
│  └─ cache/                 # .gitignore
├─ frontend/  index.html · styles.css · app.js · render.js · overlay.js · spectrum.js
├─ spikes/    01_tap.py · 02_fetch.py · 03_wcs.py · 04_gaia.py · 05_targets.py
├─ tests/
└─ docs/      spike_report.md · demo/ · submission.md
```

---

## 6. Özellik listesi (MoSCoW)

**MUST: MVP, bunlar olmadan teslim yok**
- [ ] RA/Dec girişi (ondalık ve sexagesimal) + isimle arama
- [ ] FOV seçimi
- [ ] Epoch blink: dedektör bazlı (D1…D6) ve "tüm bantlar"
- [ ] Hız, stretch/kontrast, colormap, invert, zoom kontrolleri
- [ ] Gaia DR3 overlay: konumlar her karede gözlem tarihine taşınır
- [ ] URL parametreleriyle paylaşım
- [ ] Kare metadata'sı: tarih, dedektör, λ aralığı, pozlama sayısı, sürüm
- [ ] Veri olmayan bölge veya kısmi veri için anlaşılır hata durumları

**SHOULD: güçlü bir teslim için**
- [ ] Fark modu (epoch − referans) ve Toplam modu
- [ ] **Anında spektrum** (tıklanan nokta, 0.75–5 µm, hata çubukları, bayraklı noktalar işaretli) *(ekstra puan)*
- [ ] Işık eğrisi (RW Aur, R Dra)
- [ ] FLAGS maske katmanı (bit seçimiyle)
- [ ] RGB sahte renk (D1 mavi, D3 yeşil, D6 kırmızı; soğuk kahverengi cüceler kırmızı görünür)
- [ ] Aladin Lite bağlam paneli + WISE overlay
- [ ] Tek pozlama modu (asteroitler için)
- [ ] GIF dışa aktarma, `/embed` görünümü
- [ ] Herkese açık deploy, ABD doğuda (S3'e yakın). Faz 1'de yükseltildi: yerel bağlantı ~0.65 MB/s, oysa tarayıcıya sadece ~15 KB'lık kareler gidiyor.

**COULD: zaman kalırsa**
- [ ] Molekül filtresi ön ayarları: su buzu 3.05 µm, CH₄ / PAH 3.3 µm, CO₂ 4.27 µm, CO 4.67 µm, Paα 1.875 µm, Brα 4.05 µm
- [ ] "Gaia'da olmayan kırmızı kaynak" vurgulaması (kahverengi cüce adayı)
- [ ] SkyBoT ile bilinen asteroit overlay'i
- [ ] Spektrum grafiğinde moleküler bant etiketleri
- [ ] "Aday bildir" butonu (koordinat + kareler + not, JSON veya GitHub issue)

**WON'T: bu hackathon'da yok**
Tüm gökyüzü mozaiği üretmek, kendi kaynak çıkarma pipeline'ı, kullanıcı hesapları, ML ile otomatik tespit.

---

## 7. Zaman çizelgesi (48 saat)

T+0 = başlangıç. Saatler yerel etkinlik takvimine göre kaydırılabilir.

### Faz 0: Kurulum ✅ (14.11)
- [x] Python 3.12.10 ve Git 2.56 (winget)
- [x] `.venv` + sabit sürümlü `requirements.txt`
- [x] Klasör iskeleti, `git init`, `.gitignore`, `.gitattributes`
- [x] `/api/health` uçtan uca çalışıyor
- [ ] İlk commit (Git kimliği bekleniyor)

### Faz 1: Veri spike'ı ✅ (14.11) ayrıntılar: [docs/spike_report.md](docs/spike_report.md)
- [x] `01_coverage.py`: 5 hedefin kapsamı, PM ile konum taşıma
- [x] `02_fetch.py` / `02b_range.py`: indirme yöntemleri karşılaştırması → kendi Range okuyucumuz + S3
- [x] `03_wcs.py`: konumsal + spektral WCS doğru; WCS-WAVE tablosu dedektör başına sabit
- [x] `04_gaia.py`: MAST GaiaDR3.Cone çalışıyor; astroquery `version=3` DR2'ye düşüyor; ESA TAP yedek
- [x] `05_blink.py`: uçtan uca blink prototipi. Barnard D6'da hareket görünüyor, Gaia dairesi takip ediyor.
- **Kararlar:**
  - S3 Range okuma (IMAGE + FLAGS)
  - varsayılan FOV 5′
  - dönem ve dedektör başına en fazla 4 görüntü (ayarlanabilir)
  - 60 günden uzun dönem kümeleri ~30 günlük kutulara bölünür
  - backend ABD doğuda deploy edilir

### Faz 2: Backend MVP ✅ (14.11)
- [x] `spherex/`:
  - `fits_range.py` (Range okuyucu, RICE FLAGS, düzen önbelleği)
  - `tap.py` (önbellekli, sürümler config'den)
  - `epochs.py` (boşluk + derin alan bölmesi)
  - `cutouts.py` (S3 → IRSA yedeği)
  - `wave.py` (dedektör başına spektral WCS)
  - `coadd.py`
  - `frames.py`
- [x] `catalogs/`:
  - `gaia.py` (MAST DR3 → ESA TAP yedeği, kalıcı önbellek)
  - `resolve.py` (koordinat ayrıştırma → Sesame → gömülü hedef listesi, PM ile 2026.0'a taşıma)
- [x] `app.py`:
  - `/api/config`, `/api/resolve`, `/api/observations`, `/api/gaia`
  - `/api/frames` (NDJSON akışı: `meta` → kareler → `done`)
- [x] Doygun yıldız merkezleri artık beyaz çiziliyor (Barnard D2'de NaN = 0)
- [x] 22 birim testi (`pytest`): Range okuyucu sentetik bir SPHEREx benzeri dosyaya karşı test ediliyor
- **Sonuç:** Barnard için 6 dedektör × 3 dönem + 3 "tüm bantlar" karesi.
  - İlk seferde ~38 sn, önbellekten ~3 sn.
  - Akış toplamı 274 KB (kare başına 12.5 KB).
  - Gaia: ilk sorgu 16 sn, sonra anında.
- Not: Windows'ta `localhost` IPv6 denemesi istek başına ~2 sn ekliyor; testlerde `127.0.0.1` kullan.

### Faz 3: Frontend MVP ✅ (14.11)
- [x] Yerleşim (masaüstü + mobil), build adımı yok:
  - `index.html`, `styles.css`
  - `app.js` (durum, akış, oynatıcı, URL)
  - `render.js` (stretch + colormap)
  - `sky.js` (TAN projeksiyonu, PM)
  - `overlay.js`
- [x] Kareler NDJSON akışıyla geldikçe gösteriliyor. Seçili bant yüklenene kadar önizleme gösteriliyor; ilerleme çubuğu var.
- [x] Stretch: asinh/lineer/sqrt/log, siyah/beyaz nokta (yüzdelik), yumuşatma. Bir bandın tüm kareleri **ortak** stretch kullanıyor.
- [x] Colormap gray/inferno/viridis/ice, invert, zoom, smooth. Klavye: boşluk / ← / →.
- [x] Gaia DR3 overlay her karenin tarihine taşınıyor. Renkler: kırmızı >1″/yıl, turuncu 0.1–1″/yıl, mavi diğerleri. G limiti ayarlanabilir.
- [x] Hedefin katalog hareketiyle beklenen konumu: kaynağı örtmeyen sarı nişangah. WISE 0855 gibi Gaia'da olmayan cisimler için.
- [x] Tıklayınca bilgi kutusu (Gaia kaynağı / hedef / koordinat) ve SIMBAD, WiseView, Legacy Survey, VizieR linkleri.
- [x] Fare konumunda RA/Dec + piksel değeri.
- [x] Tüm durum URL'de, paylaşım butonu var, `?embed=1` sadece oynatıcıyı gösteriyor. Tarayıcı geri/ileri tuşları çalışıyor.
- [x] Backend iyileştirmeleri:
  - aynı anda en fazla 2 dedektör indiriliyor (ilk kareler daha erken geliyor)
  - istek başına kesit bütçesi (`max_cutouts: 120`), derin alanlar için
  - dedektör sırası korunuyor
- **🎯 MVP kilometre taşı geçildi:**
  - Barnard's Star tarayıcıda blink'te kuzeye kayıyor ve Gaia halkası onu takip ediyor (önbellekten 2.6 sn).
  - WISE 0855: D6'da nişangahın ortasında, Gaia karşılığı yok (ilk yükleme 64 sn).

**Uyku / mola (T+18 → T+24)**

### Faz 4: Keşif özellikleri ✅ (14.11)
- [x] **Blink / Fark / Toplam** modları (tarayıcıda hesaplanıyor):
  - Fark: her dönem eksi tüm dönemlerin piksel medyanı. Turuncu/mavi ıraksak renk, ±5σ ölçek. Barnard'da klasik dipol görünüyor.
  - Toplam: tüm dönemlerin ortalaması, daha derin görüntü.
- [x] **RGB sahte renk** (R=D6, G=D3, B=D1; her bant kendi stretch'iyle)
- [x] Tek pozlama modu (zaten vardı; tarayıcıdan ve API'den doğrulandı)
- [x] **Işık eğrisi:** tıklanan kaynakta her dönem coadd'ı üzerinde açıklık fotometrisi. Ek indirme yok, hareketli kaynakları takip ediyor. R Dra'da Mira döngüsü görünüyor.
- [x] **Anında spektrum** *(ekstra puan)*:
  - `/api/spectrum` NDJSON akışı, `photometry.py`: photutils açıklık + halka, mJy, λ dedektör pikselinden.
  - "Quick" modu blink için zaten indirilmiş pozlamaları kullanıyor (~2.5 sn, ~70 nokta).
  - "Full" modu bir dönemin tüm pozlamalarını kullanıyor (102 kanalın tamamı).
  - Grafikte molekül bantları işaretli. WISE 0855'te 3.3–3.6 µm metan çukuru görünüyor.
- [x] **CatWISE2020 overlay'i** (IRSA Gator; TAP 95 sn sürüyordu). Hareketliler kalın elmasla, W1−W2 > 1.5 için "soğuk kahverengi cüce rengi" notu. WISE 0855 CatWISE'da 8.0″/yıl ile çıkıyor.
- [x] **Aladin Lite bağlam paneli:** 2MASS, AllWISE, SPHEREx DR1 küpü, SDSS, DSS2. CDS kapalı olduğu için IRSA'daki HiPS aynaları kullanılıyor. Alan sınırı çiziliyor.
- [x] **GIF dışa aktarma:** tarayıcı kareleri overlay'leriyle çiziyor, `/api/export/gif` Pillow ile birleştiriyor.
- [x] Bağlantı kapanınca bekleyen indirmeler iptal ediliyor (bant genişliği tasarrufu).
- [x] 25 birim testi geçiyor.
- [ ] FLAGS piksel katmanı: yapılmadı. Bayrak özeti kare bilgisinde ve spektrumda boş noktalar olarak gösteriliyor.

### Faz 5: Doğrulama ve cila ✅ (14.11, deploy hariç)
- [x] **5 test hedefi tarayıcıda uçtan uca doğrulandı.** Ekran görüntüleri `docs/screenshots/` klasöründe.

  | Hedef | Dönem | Ne görünüyor |
  |---|---|---|
  | Barnard's Star | 3 | Yıldız kuzeye kayıyor, Gaia halkası takip ediyor, arka plan yıldızları Gaia dairelerine oturuyor. Fark modunda dipol. |
  | Epsilon Indi B | 4 | D6'da parlak kahverengi cüce çifti, Gaia halkası (G=18) ve nişangah üst üste. |
  | WISE 0855 | 3 | D6'da soluk kaynak, Gaia'da yok. CatWISE'da 8.0″/yıl, W1−W2=3.8. Spektrumda 3.3 µm metan çukuru. |
  | RW Aurigae | 3 | Işık eğrisi: D5/D6'da 2700 → 1300 mJy sönükleşme. |
  | R Draconis | 17 (derin alan) | Işık eğrisinde Mira döngüsü. CatWISE alanı boş (parlak yıldız maskesi). |
- [x] `scripts/warm_cache.py`: demo öncesi 5 hedefi (kareler, Gaia, CatWISE, hızlı spektrum) önceden yüklüyor. Tüm hedefler önbellekten 2–3 sn.
- [x] Önbellekteki kesitler indirme havuzunda beklemiyor (`fetch_async`, cache-only hızlı yol). Biri yeni hedef yüklerken diğerleri yavaşlamıyor.
- [x] Varsayılan kontrast: beyaz nokta en fazla gürültünün 40σ üstü. Parlak yıldız alanlarında arka plan görünüyor; beyaz nokta %100'de sınır kalkıyor.
- [x] Hızlı hareketliler (≥0.5″/yıl) Gaia G limitinden bağımsız hep gösteriliyor. Alan kartında "Fast movers in this field" listesi var; tıklayınca nişangah ve ışık eğrisi açılıyor.
- [x] 5 hedef gömülü listeden anında çözülüyor (CDS'ten bağımsız). Bulunamayan isim 1 gün önbellekte tutuluyor, hata mesajı gösteriliyor.
- [x] Sağlamlık:
  - doygun merkezlerde NaN spektrum noktası artık oluşmuyor
  - boş katalog yanıtları kalıcı önbelleğe yazılmıyor
  - CatWISE yeniden deneme
- [x] Deploy hazırlığı: `Dockerfile`, `.dockerignore`, `docs/deploy.md` (Hugging Face Spaces / herhangi bir Docker host). Docker yerelde kurulu değil, imaj test edilmedi.
- [x] 27 birim testi geçiyor.
- [ ] **Herkese açık deploy:** hesap gerektiriyor, kullanıcı kararı bekleniyor.
- Bilinen sınırlamalar:
  - Güneş Sistemi cisimleri isimle aranamıyor (JPL Horizons entegrasyonu yok).
  - Uvicorn `--reload` Windows'ta takılabildiği için kaldırıldı.

### Faz 6: Teslim ✅ hazır, ekip bilgisi ve linkler bekleniyor (14.11)
- [x] Teslim kuralları "Project Submission Guide"dan teyit edildi:
  - son teslim **15 Kasım Pazar 23:59, yerel etkinlik saatiyle**
  - demo = **en fazla 7 slayt** veya **en fazla 30 sn video**, herkese açık link
  - her şey İngilizce
  - **SI (Super Intelligence) kullanımı** beyan edilmeli; SI üretimi kod "açıklama metni ve metadata" ile belirtilmeli
- [x] `README.md` jüri için yeniden yazıldı: özellikler, 5 hedefin sonuçları, nasıl çalıştığı, API, kurulum, sınırlamalar, SI bölümü, veri teşekkürleri
- [x] `SI_DISCLOSURE.md` + tüm kaynak dosyalarda (40 dosya) SI başlık satırı
- [x] `docs/submission.md`: formun her alanı için yapıştırmaya hazır İngilizce metin
- [x] `docs/demo.md`: 30 sn video senaryosu, 2–3 dk canlı demo akışı, slayt taslağı
- [x] 7 slaytlık sunum (Claude Slides): https://claude.ai/artifact/CbsPTZUBHtWgkeokzBamrJ
  - görseller gerçek SPHEREx verisinden (`scripts/render_strip.py`, `docs/slides/`)
  - her slaytta SI notu var
- [ ] Ekip adı ve üye isimleri (slayt 1, README, submission)
- [ ] Sunumu paylaşıma açma veya PDF olarak dışa aktarıp herkese açık bir yere koyma
- [ ] GitHub reposu (veya başka herkese açık link) → "Link to Final Project"
- [ ] Space Apps sayfasına metinleri girip "Submit for Judging"

---

## 8. Riskler ve önlemler

| Risk | Etki | Önlem |
|---|---|---|
| Veri transfer hacmi/gecikmesi. Ölçülen: yerel ~0.65 MB/s, ~0.5 MB/görüntü; 72 görüntü ≈ 1 dk | Yavaş arayüz | S3 Range okuma (seçildi), dönem başına kare limiti, kademeli yükleme (SSE), diskcache, demo önbelleği, backend ABD doğuda deploy |
| IRSA TAP yavaş (7–18 sn), cutout servisi 503 | Gecikme / kesinti | TAP sonuç önbelleği, cutout servisi sadece son yedek |
| Doygun yıldız merkezleri NaN geliyor (Barnard D2) | Yıldız ortası siyah görünür | Kaynak içi NaN'ları "doygun" (beyaz) çiz, doygunluk bitlerini maskeleme |
| Eski epoch koordinatları (hızlı yıldızlar) | Hedef karede görünmez | PM ile konum taşıma, geniş varsayılan FOV, kullanıcıya uyarı |
| LVF: aynı dedektörde pozlamalar farklı λ'da | Renk farkı değişkenlik gibi görünebilir | Dedektör coadd'ında λ aralığını göster, "dar kanal" seçeneği, spektrumla doğrulama |
| Parlak yıldız doygunluğu ve hayaletler (Barnard, Eps Indi A) | Yanıltıcı görüntü | FLAGS maskesi, flag katmanı, metadata'da uyarı |
| 6″ piksel, 1 px civarı hareket (Eps Indi B) | Gözle zor fark edilir | Fark modu (dipol), yumuşak zoom, Gaia oku |
| IRSA/MAST kesintisi | Demo çöker | Retry + backoff, önbellek, Gaia yedekleri (ESA TAP, VizieR), önceden kaydedilmiş demo videosu |
| MAST Gaia DR3 sütun/sürüm belirsizliği | Overlay eksik kalır | Faz 1'de test, adaptör katmanı |
| Ortam (Python/Git/Node yok) | Zaman kaybı | Faz 0 winget kurulumu, Node gerektirmeyen frontend |

---

## 9. Demo senaryosu (~30 sn video veya sunum akışı)
1. **Barnard's Star** linkine tıkla: yıldız kareler boyunca kayıyor, Gaia dairesi onu takip ediyor.
2. **WISE 0855:** D1'de boş, D6'da parlak bir nokta. Gaia'da karşılığı yok ve hareket ediyor. Tıkla, spektrumda soğuk atmosfer imzası görünüyor.
3. **R Draconis:** epoch'lar arasında parlaklık değişimi ve ışık eğrisi.
4. **Fark modu:** Epsilon Indi B'nin dipol deseni.
5. Bir URL'yi başka bir sayfaya `/embed` ile gömme.

---

## 10. Açık sorular (başlamadan netleşmesi iyi olur)
- Takım kaç kişi? Faz 2 ve Faz 3 paralel yürüyebilir mi?
- Yerel etkinliğin teslim saati tam olarak ne?
- Herkese açık deploy gerekli mi, yoksa lokal demo + video yeterli mi?
- Arayüz dili: **İngilizce önerilir** (global jüri), Türkçe seçeneği opsiyonel.

---

## 11. Kaynaklar
- Challenge: https://www.spaceappschallenge.org/2026/challenges/planet-x-and-spherex/
- IRSA SPHEREx: https://irsa.ipac.caltech.edu/Missions/spherex.html
- SPHEREx arşiv dokümantasyonu: https://irsa.ipac.caltech.edu/spherex-archive-documentation/
- Tutorial notebook'ları: https://caltech-ipac.github.io/irsa-tutorials/spherex/
  - intro, cutouts, psf, source-discovery-tool-demo, mosaic, hipscube
- Explanatory Supplement (PDF): https://irsa.ipac.caltech.edu/data/SPHEREx/docs/SPHEREx_Expsupp.pdf
- S3 tarayıcı: https://nasa-irsa-spherex.s3.us-east-1.amazonaws.com/index.html
- Gaia (MAST): https://archive.stsci.edu/missions-and-data/gaia
- MAST API servisleri: https://mast.stsci.edu/api/v0/_services.html
- WiseView: http://byw.tools/wiseview
  - Tanıtım yazısı: https://blog.backyardworlds.org/2017/09/13/wiseview/
  - ASCL kaydı: https://ascl.net/1806.004
- Aladin Lite: https://aladin.cds.unistra.fr/AladinLite/
