var weekly_quakes_endpoint = "earthquake_data.json";

var map;
var openInfoWindow; // Şu an açık olan bilgi penceresi

$(document).ready(function(){

  map = new google.maps.Map(document.getElementById('map'), {
    center: {lat: 38.9334, lng: 34.8597},
    zoom: 6
  });

  // Verileri çekmek ve işaretlemek için işlev
  function getAndMarkEarthquakeData() {
    $.getJSON(weekly_quakes_endpoint, function(data) {
      var earthquakes = Object.values(data); // JSON'daki nesneleri bir diziye dönüştür

      for (var i = 0; i < earthquakes.length; i++) {
        var earthquake = earthquakes[i];
        var latLng = new google.maps.LatLng(parseFloat(earthquake.latitude), parseFloat(earthquake.longitude));

        // İşaretçi oluştur
        var marker = new google.maps.Marker({
          position: latLng,
          map: map,
          title: earthquake.location
        });

        // Bilgi penceresi içeriği
        var contentString = "Yer: " + earthquake.location +
         "<br>Enlem: " + earthquake.latitude +
         "<br>Boylam: " + earthquake.longitude +
         "<br>Derinlik: " + earthquake.depth + 
         "<br>Büyüklük: " + earthquake.magnitude +
         "<br>Tarih: " + earthquake.date;

        // İşaretçiye tıklanınca bilgi penceresi göster
        attachInfoWindow(marker, contentString);
      }
    });
  }

  // İşaretçiye tıklanınca bilgi penceresi gösterme işlevi
  function attachInfoWindow(marker, content) {
    var infoWindow = new google.maps.InfoWindow({
      content: content
    });

    marker.addListener('click', function() {
      // Önceki bilgi penceresini kapat
      if (openInfoWindow) {
        openInfoWindow.close();
      }
      
      // Yeni bilgi penceresini göster
      infoWindow.open(marker.get('map'), marker);
      openInfoWindow = infoWindow;
    });
  }

  // Verileri çek ve işaretle
  getAndMarkEarthquakeData();
});
