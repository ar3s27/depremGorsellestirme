var weekly_quakes_endpoint = "https://deprem.afad.gov.tr/EventData/GetLast5Events";

var map;

$(document).ready(function(){

  map = new google.maps.Map(document.getElementById('map'), {
    center: {lat: 38.9334, lng: 34.8597},
    zoom: 6
  });

  // Verileri çekmek ve işaretlemek için işlev
  function getAndMarkEarthquakeData() {
    $.getJSON(weekly_quakes_endpoint, function(data) {
      var earthquakes = data;

      for (var i = 0; i < earthquakes.length; i++) {
        var earthquake = earthquakes[i];
        var latLng = new google.maps.LatLng(earthquake.latitude, earthquake.longitude);

        // İşaretçi oluştur
        var marker = new google.maps.Marker({
          position: latLng,
          map: map,
          title: earthquake.location
        });

        marker.addListener('click', function() {
          infoWindow.open(map, marker);
        });
      }
      // İşaretçiye tıklanınca bilgi penceresi göster
      var infoWindow = new google.maps.InfoWindow({
        content: "Location: " + earthquake.location + "<br>Magnitude: " + earthquake.magnitude
      });
    });
  }

  // Verileri çek ve işaretle
  getAndMarkEarthquakeData();
});
