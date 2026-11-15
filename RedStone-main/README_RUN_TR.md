# SPHEREview'i başka bilgisayarda çalıştırma

## Gerekenler

- Python 3.12
- İlk açılışta Python paketlerini indirmek, görüntüleri NASA arşivinden almak ve katalog sorguları için internet bağlantısı
- Windows'ta `.bat` dosyasını çalıştırma izni; macOS/Linux'ta Terminal

API anahtarı gerekmez. Görüntü ve katalog verileri NASA/IPAC IRSA, MAST, Gaia ve JPL'nin herkese açık kaynaklarından çalışma sırasında alınır. İlk açılış paketleri kurduğu için birkaç dakika sürebilir; sonraki açılışlarda kurulum atlanır. İndirilen görüntü önbelleği o bilgisayarda kalır.

## Windows

1. `SPHEREview-portable.zip` dosyasını bir klasöre çıkarın.
2. Python 3.12 kurulu değilse [python.org](https://www.python.org/downloads/) üzerinden kurun. Kurulumda PATH seçeneğini açın.
3. Klasörde `BASLAT.bat` dosyasına çift tıklayın. Mevcutsa `RUN_SPHEREVIEW.bat` da aynı başlatıcıyı kullanır.
4. Tarayıcı otomatik açılır. Açılmazsa terminalde yazan `http://127.0.0.1:...` adresini açın.
5. Uygulamayı kapatmak için siyah başlatma penceresine dönüp `Ctrl+C`'ye basın.

## macOS / Linux

Python 3.12 kurduktan sonra klasörde Terminal açıp `sh BASLAT.sh` çalıştırın. Tarayıcı otomatik açılır. Kapatmak için Terminal'de `Ctrl+C`'ye basın.

## Hata olursa

- Python 3.12 bulunamadı: Python 3.12'yi kurup başlatıcıyı yeniden açın.
- Paket kurulumu başarısız: internet bağlantısını kontrol edin, klasörde yazma izni olduğundan emin olun ve tekrar deneyin.
- NASA verisi yüklenmiyor: uygulama açıldıktan sonra internet erişimini ve NASA/IRSA servislerinin durumunu kontrol edin. İlk bir alanın indirilmesi daha uzun sürebilir (15′ alan, 5′ alana göre yaklaşık 9 kat fazla veri indirir).
- NASA/IRSA poz arama servisi yanıt vermezse (30 sn içinde; arıza sürerken 8 sn) uygulama boş kalmaz: aynı koordinat için **SPHEREx DR1 tüm gökyüzü küpü** (102 kanal, ~13″, tek dönem) gösterilir ve tayf da bu küpten ölçülür. Bu modda dönemler arası değişim/aday analizi yapılamaz; arşiv sorgusu arka planda sürer ve sonucu önbelleğe yazılır, aynı alanı birkaç dakika sonra yeniden araştırınca çok dönemli görüntüler gelir.
- Koordinatlarda ondalık ayırıcı olarak virgül veya nokta kullanılabilir (`279,7598787` / `-6,0862599`); `18:39:02.4` / `-06:05:10` biçimi de kabul edilir.
- Başka uygulama 8000 numaralı portu kullanıyorsa başlatıcı 8001–8020 arasındaki boş bir portu otomatik seçer.

`start.py`, aynı proje klasöründe `.venv` ortamını kurar; sistem Python kurulumunu değiştirmez. `backend/cache` altında oluşan veriler performans önbelleğidir ve kaynak arşivine dahil edilmez.

## Ölçüm arşivi ve grafik uyumları

Araştırma bitince aday ölçümleri, dönem tarihleri, koordinatlar, katalog eşleşmeleri, kanıt puanları ve görüntüleyicide gösterilen işlenmiş kareler tarayıcının yerel IndexedDB arşivine otomatik yazılır (son 25 araştırma). Kaydı daha sonra görüntü kareleriyle açabilir, CSV/JSON indirebilir veya JSON'u başka bilgisayarda içe aktarabilirsiniz. NASA arşivindeki özgün tam FITS dosyaları aktarılmaz; JSON dosyası görüntü karelerini de içerdiği için büyük olabilir.

Aday izleri ekranında konum ve parlaklık grafiklerinin her biri için **En uyumlu**, **Ham veri**, **Sabit**, **Doğrusal** ve **İkinci derece** seçimleri bulunur. Otomatik seçenek ölçümlere göre BIC'i en düşük modeli seçer; R² ve RMSE de gösterilir. Ayrıca minimum puan, gözlem dönemi, tepe anlamlılığı ve en büyük uyum artığı ölçütleriyle aday listesini daraltabilirsiniz. Az sayıda dönemle karmaşık model seçmek aşırı uyuma yol açabileceği için grafik ölçütlerini ve ham noktaları birlikte inceleyin.
