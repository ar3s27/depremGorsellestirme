import uvicorn
from fastapi import FastAPI
import requests as re
from bs4 import BeautifulSoup

app = FastAPI(title="Earthquake")

@app.get('/')
def earthquake():
    url = "https://deprem.afad.gov.tr/last-earthquakes.html"
    response = re.get(url)
    soup = BeautifulSoup(response.content, "html.parser")

    try:
        table = soup.find("table", class_="k-grid-table")
        tbody = table.find("tbody", kendogridtablebody="")
        rows = tbody.find_all("tr", class_="ng-star-inserted")

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
    uvicorn.run(app, host="127.0.0.1", port=7000)
