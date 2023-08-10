import csv



csv = "earthquake_data.csv"

# CSV dosyasını yazma modunda açın ve başlık satırını yazın
with open(csv, mode='w', newline='') as file:
    writer = csv.writer(file)
    writer.writerow(["Yer", "Enlem", "Boylam", "Derinlik", "Büyüklük", "Tarih"])

    # Sözlüğün içindeki verileri CSV dosyasına ekleyin
    for quake_id, data in kutuphane.items():
        writer.writerow([
            data["location"],
            data["latitude"],
            data["longitude"],
            data["depth"],
            data["magnitude"],
            data["Tarih"]
        ])

print(f"Veriler {csv} dosyasına başarıyla eklendi.")
