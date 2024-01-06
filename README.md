# Deprem Görselleştirme Uygulaması

Bu uygulama, AFAD'ın [deprem verileri](https://deprem.afad.gov.tr/last-earthquakes.html)ni çekerek harita üzerinde görselleştiren bir projedir. Verileri çekip işleyen backend tarafı FastAPI kullanılarak yazılmıştır, ön tarafta ise JavaScript ve Google Maps API kullanılarak harita ve tablo oluşturulmaktadır.

## Dosyalar ve Kullanılan Teknolojiler

1. **Base.js**: Harita ve deprem verilerini çekip işleyen JavaScript dosyası.

2. **index.html**: Kullanıcı arayüzü ve harita görüntüsü sağlayan HTML dosyası.

3. **app.py**: FastAPI ile yazılmış backend tarafını içeren Python dosyası.

4. **vercel.json**: Vercel dağıtımı için yapılandırma dosyası.

## Kullanım

1. Proje dosyalarını indirin.
2. `index.html` dosyasını bir tarayıcıda açarak harita ve deprem bilgilerini gözlemleyebilirsiniz.
3. Backend tarafını başlatmak için `app.py` dosyasını çalıştırın (yorum satırındaki kodu açmanız gerekebilir).

## Gereksinimler

- [FastAPI](https://fastapi.tiangolo.com/)
- [Requests](https://docs.python-requests.org/en/latest/)
- [BeautifulSoup](https://www.crummy.com/software/BeautifulSoup/)
- [Google Maps API Key](https://developers.google.com/maps/gmp-get-started)

## Lisans

Bu proje açık kaynaklıdır ve [MIT lisansı](LICENSE) altında dağıtılmaktadır. Detaylı bilgi için lisans dosyasını inceleyebilirsiniz.