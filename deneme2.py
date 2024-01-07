import uvicorn
from fastapi import FastAPI
from selenium import webdriver
from bs4 import BeautifulSoup

app = FastAPI(title="Earthquake")

@app.get('/')
def earthquake():from fastapi import FastAPI
from fastapi.responses import JSONResponse
import uvicorn
from bs4 import BeautifulSoup
from fastapi.middleware.cors import CORSMiddleware
import time
import json
from selenium import webdriver

app = FastAPI(title="Earthquake")
app.add_middleware(
    CORSMiddleware,
    allow_origins=['*']
)

def save_to_json(data):
    with open('earthquake_data.json', 'w', encoding='utf-8') as json_file:
        json.dump(data, json_file, ensure_ascii=False, indent=4)

def read_json():
    try:
        with open('earthquake_data.json', 'r', encoding='utf-8') as json_file:
            data = json.load(json_file)
        return data
    except FileNotFoundError:
        return {}

kutuphane = {}

@app.get('/')
def earthquake():
    while True:
        url = "https://deprem.afad.gov.tr/last-earthquakes.html"
        # Use Selenium to load the dynamic content
        driver = webdriver.Chrome()
        driver.get(url)

        # Add a delay to wait for JavaScript to execute
        time.sleep(5)  # Adjust the delay as needed

        page_source = driver.page_source
        driver.quit()

        soup = BeautifulSoup(page_source, "html.parser")

        try:
            table = soup.find("table", class_="k-grid-table")
            tbody = table.find("tbody", kendogridtablebody="")
            rows = tbody.find_all("tr")

            earthquakes = []

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
                        print("Yer: " + location)
                        print("Enlem: " + latitude)
                        print("Boylam: " + longitude)
                        print("Derinlik: " + depth)
                        print("Büyüklük: " + magnitude)
                        print("Tarih: " + date)
                        print("\n")

                        earthquake_info = {
                            'quake_id': quake_id,
                            "location": location,
                            "latitude": latitude,
                            "longitude": longitude,
                            "depth": depth,
                            "magnitude": magnitude,
                            "date": date
                        }

                        earthquakes.append(earthquake_info)
                        kutuphane[quake_id] = earthquake_info
            
            save_to_json(kutuphane)
            time.sleep(10)  # Sleep for 10 minutes before the next update
            return {"earthquake": earthquakes}

        except AttributeError:
            print("Table not found. Check the website structure.")
            return {"error": "Table not found. Check the website structure."}

@app.get('/show_saved_json')
def show_saved_json():
    data = read_json()
    return JSONResponse(content=data)

if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8000)

    url = "https://deprem.afad.gov.tr/last-earthquakes.html"

    # Use Selenium to load the dynamic content
    driver = webdriver.Chrome()
    driver.get(url)
    page_source = driver.page_source
    driver.quit()

    soup = BeautifulSoup(page_source, "html.parser")

    try:
        table = soup.find("table")
        tbody = table.find("tbody", kendogridtablebody="")
        rows = tbody.find_all("tr")

        for row in rows:
            columns = row.find_all("td")
            date = columns[0].text.strip()
            latitude = columns[1].text.strip()
            longitude = columns[2].text.strip()
            depth = columns[3].text.strip()
            magnitude = columns[5].text.strip()
            location = columns[6].text.strip()
            quake_id = columns[7].text.strip()

            print("Yer:", location)
            print("Enlem:", latitude)
            print("Boylam:", longitude)
            print("Derinlik:", depth)
            print("Büyüklük:", magnitude)
            print("Tarih:", date)
            print("\n")

    except AttributeError:
        print("Table not found. Check the website structure.")

if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8000)