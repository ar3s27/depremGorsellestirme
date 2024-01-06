import uvicorn
from fastapi import FastAPI
import requests as re
from bs4 import BeautifulSoup
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(title="Earthquake")
app.add_middleware(
    CORSMiddleware,
    allow_origins=['*']
)

kutuphane = {}


def extract_earthquake_data(html_code):
    soup = BeautifulSoup(html_code, 'html.parser')
    earthquake_data = []

    # Assuming you want to extract data from the cells, you can loop through the rows and columns
    for row in soup.find_all('tr', class_='ng-star-inserted'):
        columns = row.find_all('td')
        quake_id = columns[7].text.strip()

        if quake_id in kutuphane:
            continue

        earthquake_data.append({
            'quake_id': quake_id,
            'location': columns[6].text.strip(),
            'latitude': columns[1].text.strip(),
            'longitude': columns[2].text.strip(),
            'depth': columns[3].text.strip(),
            'magnitude': columns[5].text.strip(),
            'date': columns[0].text.strip()
        })

    return earthquake_data


@app.get('/')
def earthquake():
    url = "https://deprem.afad.gov.tr/last-earthquakes.html"
    response = re.get(url)
    html_code = response.content

    try:
        earthquake_data = extract_earthquake_data(html_code)

        for quake in earthquake_data[:11]:
            quake_id = quake['quake_id']

            if quake_id not in kutuphane:
                print("Yer:", quake['location'])
                print("Enlem:", quake['latitude'])
                print("Boylam:", quake['longitude'])
                print("Derinlik:", quake['depth'])
                print("Büyüklük:", quake['magnitude'])
                print("Tarih:", quake['date'])
                print("\n")

                kutuphane[quake_id] = quake

        return kutuphane

    except AttributeError:
        print("Table not found. Check the website structure.")


if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=7000)
