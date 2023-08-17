import requests as re
from bs4 import BeautifulSoup as bs
import time
import csv
import pandas as pd
import folium
import webbrowser

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
        
        # CSV dosyasını yazma modunda açın ve başlık satırını yazın
        csv_filename = "earthquake_data.csv"
        
        # Sadece yeni verileri eklemek istediğinizden emin olun
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
        
        # Read the CSV file using pandas
        data = pd.read_csv(csv_filename, encoding='cp1254')  # veya encoding='cp1254'

        # Take the last ten records
        last_ten = data.tail(10)

        # Create a map centered at the mean latitude and longitude
        m = folium.Map(location=[last_ten['latitude'].mean(), last_ten['longitude'].mean()], zoom_start=6)

        # Add markers for each earthquake
        for index, row in last_ten.iterrows():
            folium.Marker(
                location=[row['latitude'], row['longitude']],
                popup=f"{row['location']}<br>Magnitude: {row['magnitude']}<br>Depth: {row['depth']} km",
                icon=folium.Icon(color='red')
            ).add_to(m)

        # Save the map as an HTML file
        map_filename = "earthquake_map.html"
        m.save(map_filename)

        print(f"Harita {map_filename} dosyasına başarıyla kaydedildi.")

        # Open the map in the default web browser
        webbrowser.open(map_filename)

    except AttributeError:
        print("Table not found. Check the website structure.")
    except Exception as e:
        print("An error occurred:", str(e))