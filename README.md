# Sismik — Türkiye canlı deprem haritası

**Canlı:** https://deprem.veyselerkoyuncu.com.tr

AFAD'ın deprem kayıtlarını dakikada bir çeken, kendi veritabanında biriktiren ve bunları
harita, sismogram şeridi, liste, açık API ve Telegram botu olarak sunan tek bir servis.

- **Harita:** her deprem büyüklüğüne göre boyutlanan ve renklenen bir nokta; son bir saatin
  depremleri nabız gibi atar, eskiyenler soluklaşır.
- **Sismogram şeridi:** seçili aralıktaki her deprem, zamanına denk gelen yerde büyüklüğüyle
  orantılı bir dalga olarak çizilir. Dalganın üstüne gelmek ya da tıklamak depremi seçer.
- **Canlı akış:** yeni depremler sayfayı yenilemeden gelir (Server-Sent Events); 3 ve üzeri
  için bildirim çıkar.
- **Ayrıntı:** saat (TSİ ve UTC), derinlik, koordinat, 50 km çevresindeki öncü ve artçı
  depremler, paylaşılabilir bağlantı, AFAD kaydı.
- **Telegram botu:** son depremler, yakınındaki depremler (konum gönder), büyüklük eşiğine göre
  anlık uyarı aboneliği.

## Mimari

```
              ┌────────────────────── deprem konteyneri ──────────────────────┐
AFAD JSON ──► │ Toplayıcı ─► SQLite (/data) ─► REST API  ─► /api/quakes …     │
  (60 sn)     │     │                                                         │
              │     └─► Yayın merkezi ─┬─► SSE ─────────► /api/stream         │
              │                        └─► Telegram botu ─► abonelere uyarı   │
              │ Derlenmiş ön yüz (React + MapLibre) ─────► /                  │
              └───────────────────────────────────────────────────────────────┘
```

- **backend/** — Python 3.12, FastAPI, httpx, aiogram 3, SQLite (WAL).
  - `afad.py`: AFAD istemcisi. Servis tek istekte en fazla 1000 olay döndürür; dolu gelen
    pencereler ikiye bölünerek yeniden istenir.
  - `collector.py`: açılışta geçmişi doldurur (varsayılan 14 gün), sonra dakikada bir son 24
    saati çeker; yeni ve güncellenen depremleri yayın merkezine bildirir.
  - `store.py`: depremler ve bot aboneleri. AFAD yalnızca son ~1000 olayı tuttuğu için uzun
    geçmiş burada birikir.
  - `main.py`: API, SSE, güvenlik başlıkları ve ön yüzün sunulması.
  - `bot.py`: Telegram botu; `TELEGRAM_BOT_TOKEN` boşsa hiç başlamaz.
- **frontend/** — React 19, TypeScript, Vite, MapLibre GL. Altlık OpenFreeMap'in anahtarsız
  koyu haritası, Sismik renklerine boyanır.

## API

Hepsi `GET`, CORS açık, anahtar gerekmez. Etkileşimli belgeler: [`/api/docs`](https://deprem.veyselerkoyuncu.com.tr/api/docs)

| Adres | Ne döner |
| --- | --- |
| `/api/quakes?hours=24&min_mag=0&limit=` | Son `hours` saatin depremleri, yeniden eskiye (`hours` 1–8760) |
| `/api/quakes/{id}` | Tek deprem ve 50 km çevresinde ±7 gündeki depremler |
| `/api/stream` | Canlı akış (SSE): `event: new` / `event: update`, gövde deprem JSON'ı |
| `/api/health` | Kayıt sayısı, son çekim zamanı, varsa son hata |

Örnek:

```bash
curl "https://deprem.veyselerkoyuncu.com.tr/api/quakes?hours=6&min_mag=3"
```

Zamanlar UTC ve ISO 8601 (`2026-11-07T01:24:14Z`); büyüklük, derinlik (km) ve koordinatlar
sayıdır. Eski `deprem-api.veyselerkoyuncu.com.tr` alan adı da aynı servise gelir.

## Telegram botu

| Komut | |
| --- | --- |
| `/son` | Son 10 deprem |
| `/buyukler` | Son 7 günün 4 ve üzeri depremleri |
| `/abone 4.5` | Bu büyüklük ve üzeri için anlık uyarı (varsayılan 4) |
| `/iptal` | Uyarıları kapat |
| konum gönder | 100 km çevrendeki son 7 günün depremleri |

## Geliştirme

Arka uç (Python 3.12):

```bash
cd backend
python -m venv .venv && . .venv/Scripts/activate   # Linux/macOS: . .venv/bin/activate
pip install -r requirements-dev.txt
pytest
uvicorn app.main:create_app --factory --port 8000
```

Ön yüz (Node 22), ayrı bir terminalde. Vite `/api` isteklerini 8000 portuna yönlendirir:

```bash
cd frontend
npm install
npm run dev        # http://localhost:5174
```

Ortam değişkenleri: `DB_PATH`, `POLL_SECONDS`, `BACKFILL_DAYS`, `COLLECTOR` (`0` toplayıcıyı
kapatır), `TELEGRAM_BOT_TOKEN`, `PUBLIC_URL`, `STATIC_DIR`.

## Yayın

Ev sunucusunda Docker ile çalışır; Cloudflare Tunnel `http://deprem:8000` adresine yönlendirir.

```bash
bash deploy/deploy.sh
```

Betik git'e kayıtlı dosyaları sunucuya kopyalar, imajı orada derler ve konteyneri yeniden
başlatır. Telegram token'ı sunucuda `~/apps/deprem/.env` dosyasına elle yazılır; repoya girmez.

## Kaynak ve lisans

Veriler [AFAD](https://deprem.afad.gov.tr)'a aittir; bu site resmî bir kaynak değildir. Harita
altlığı © [OpenFreeMap](https://openfreemap.org), © [OpenMapTiles](https://openmaptiles.org),
© [OpenStreetMap](https://www.openstreetmap.org/copyright) katkıcıları.

Kod MIT lisansıyla açıktır.
