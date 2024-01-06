Deprem Görselleştirme Uygulaması
Bu uygulama, AFAD'ın deprem verilerini çekerek harita üzerinde görselleştiren bir projedir. Verileri çekip işleyen backend tarafı FastAPI kullanılarak yazılmıştır, ön tarafta ise JavaScript ve Google Maps API kullanılarak harita ve tablo oluşturulmaktadır.

Dosyalar ve Kullanılan Teknolojiler
Base.js: Harita ve deprem verilerini çekip işleyen JavaScript dosyası.

index.html: Kullanıcı arayüzü ve harita görüntüsü sağlayan HTML dosyası.

app.py: FastAPI ile yazılmış backend tarafını içeren Python dosyası.

Kullanım
Proje dosyalarını indirin.
index.html dosyasını bir tarayıcıda açarak harita ve deprem bilgilerini gözlemleyebilirsiniz.
Backend tarafını başlatmak için app.py dosyasını çalıştırın (yorum satırındaki kodu açmanız gerekebilir).
Gereksinimler
FastAPI
Requests
BeautifulSoup
Google Maps API Key
Lisans
Bu proje açık kaynaklıdır ve MIT lisansı altında dağıtılmaktadır. Detaylı bilgi için lisans dosyasını inceleyebilirsiniz.