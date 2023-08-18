import requests as re
from bs4 import BeautifulSoup as bs
import time
import json

# Verileri JSON dosyasına kaydetmek
def save_to_json(data):
    with open('earthquake_data.json', 'w', encoding='utf-8') as json_file:
        json.dump(data, json_file, ensure_ascii=False, indent=4)

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

                    kutuphane[quake_id] = {
                        "quake_id": quake_id,
                        "location": location,
                        "latitude": latitude,
                        "longitude": longitude,
                        "depth": depth,
                        "magnitude": magnitude,
                        "date": date
                    }
        save_to_json(kutuphane)              
        time.sleep(60)
        
    except AttributeError:
        print("Table not found. Check the website structure.")