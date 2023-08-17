import requests as re
from bs4 import BeautifulSoup as bs
import time
import csv
import googlemaps
import folium
import webbrowser

def create_map_with_markers(data):
    harita = folium.Map(location=[39.9334, 32.8597], zoom_start=6)

    for entry in data.values():
        enlem = entry['latitude']
        boylam = entry['longitude']
        buyukluk = entry['magnitude']
        lokasyon = entry['location']

        popup_content = f"Lokasyon: {lokasyon}<br>Enlem: {enlem}<br>Boylam: {boylam}<br>Büyüklük: {buyukluk}"
        folium.Marker([enlem, boylam], popup=popup_content).add_to(harita)

    return harita

# Google Haritalar API anahtarını buraya girin
google_maps_api_key = 'AIzaSyBjIpzDgZxl7INkz8-PPFm1DrpBIVPGseI'  # Replace with your actual API key
gmaps = googlemaps.Client(key=google_maps_api_key)

kutuphane = {}

while True:
    url = "https://deprem.afad.gov.tr/last-earthquakes.html"
    response = re.get(url)
    soup = bs(response.content, "html.parser")

    try:
        table = soup.find("table")
        rows = table.find_all("tr")

        for i, row in enumerate(rows[:11]):
            cells = row.find_all("td")

            if cells:
                location = cells[6].text.strip()
                date = cells[0].text.strip()
                latitude = cells[1].text.strip()
                longitude = cells[2].text.strip()
                depth = cells[3].text.strip()
                magnitude = cells[5].text.strip()
                quake_id = cells[7].text.strip()

                if quake_id in kutuphane:
                    continue
                else:
                    print("Yer: " + location )
                    print("Enlem: " + latitude)
                    print("Boylam: " + longitude)
                    print("Derinlik: " + depth)
                    print("Büyüklük: " + magnitude)
                    print("Tarih: " + date)
                    print("\n")

                    # Lokasyon verilerini almak için Google Haritalar API kullanın
                    geocode_result = gmaps.geocode(location)
                    if geocode_result:
                        lat = geocode_result[0]['geometry']['location']['lat']
                        lng = geocode_result[0]['geometry']['location']['lng']

                        kutuphane[quake_id] = {
                            "quake_id": quake_id,
                            "location": location,
                            "latitude": lat,
                            "longitude": lng,
                            "depth": depth,
                            "magnitude": magnitude,
                            "date": date
                        }

        # Haritayı oluştur ve HTML dosyasına kaydet
        harita = create_map_with_markers(kutuphane)
        harita.save('earthquake_map.html')

        # Open the generated HTML file in the default web browser
        webbrowser.open('earthquake_map.html')

        # CSV dosyasını güncelle
        csv_filename = "earthquake_data.csv"
        existing_ids = set()

        try:
            with open(csv_filename, mode='r') as file:
                reader = csv.reader(file)
                next(reader)  # Başlık satırını atla
                for row in reader:
                    existing_ids.add(row[0])  # Id sütunundaki değerleri topla
        except FileNotFoundError:
            pass

        with open(csv_filename, mode='a', newline='') as file:
            writer = csv.writer(file)

            # Yeni verileri ekleyin, ancak zaten varsa eklemeyin
            for quake_id, data in kutuphane.items():
                if quake_id not in existing_ids:
                    writer.writerow([
                        data["quake_id"],
                        data["location"],
                        data["latitude"],
                        data["longitude"],
                        data["depth"],
                        data["magnitude"],
                        data["date"]
                    ])

        print(f"Veriler {csv_filename} dosyasına başarıyla eklendi.")
        time.sleep(60)

    except AttributeError:
        print("Table not found. Check the website structure.")
