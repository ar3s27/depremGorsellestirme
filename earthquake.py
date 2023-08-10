import requests as re
from bs4 import BeautifulSoup as bs
import time

kutuphane = []

while(True):
    url = "https://deprem.afad.gov.tr/last-earthquakes.html"
    #sitenin urlsini çekiyorum
    response = re.get(url)
    soup = bs(response.content,"html.parser")
    table = soup.find("table")
    #tablo içinden "table"'ı buluyorum
    rows = table.find_all("tr")

    #aldığım veriden 10 tanesini listeliyorum
    for i,row in enumerate(rows[:10]):
        cells = row.find_all('td')

        #6 sutün olan konumu belirleyip değişken içinde atıp ekrana yazdırıyorum
        if cells:
            location = cells[6].text.strip()
            magnitude = cells[5].text.strip()
            latitude = cells[5].text.strip()
            magnitude = cells[5].text.strip()
            longitude = cells[3].text.strip()
            date = cells[0].text.strip()
            id = cells[7].text.strip()
            
            if id in kutuphane:
                continue
            else:
                print("Yer: " + location)
                print("Büyüklük: " + magnitude)
                print("Derinlik: " + longitude)
                print("Tarih: " + date)
                print("\n")
                kutuphane.append(id)

    time.sleep(3)