var earthquake_data = "earthquake_data.json";

var map;
var openInfoWindow; // Şu an açık olan bilgi penceresi

$(document).ready(function(){

  map = new google.maps.Map(document.getElementById('map'), {
    center: {lat: 38.9334, lng: 34.8597},
    zoom: 6
  });

  // Verileri çekmek ve işaretlemek için işlev
  function getAndMarkEarthquakeData() {
    $.getJSON(earthquake_data, function(data) {
      var earthquakes = Object.values(data);
  
      var infoHTML = '<div class="row">'; // Start a Bootstrap row
  
      for (var i = 0; i < earthquakes.length; i++) {
        var earthquake = earthquakes[i];
        var latLng = new google.maps.LatLng(parseFloat(earthquake.latitude), parseFloat(earthquake.longitude));
  
        var marker = new google.maps.Marker({
          position: latLng,
          map: map,
          title: earthquake.location
        });
  
        var contentString = "Yer: " + earthquake.location +
         "<br>Enlem: " + earthquake.latitude +
         "<br>Boylam: " + earthquake.longitude +
         "<br>Derinlik: " + earthquake.depth + " km"+ 
         "<br>Büyüklük: " + earthquake.magnitude +
         "<br>Tarih: " + earthquake.date;
  
        attachInfoWindow(marker, contentString);
  
        infoHTML += '<div class="col-md-2 mb-2">'; // Create a Bootstrap column
        infoHTML += '<div class="card text-bg-warning" style="max-width: 15rem;">';
        infoHTML += '<h4 class="card-header">Büyüklük: ' + earthquake.magnitude + '</h4>';
        infoHTML += '<div class="card-body">';
        infoHTML += '<h5 class="card-title">Yer: ' + earthquake.location + '</h5>';
        infoHTML += '<p class="card-text">Enlem: ' + earthquake.latitude + '</p>';
        infoHTML += '<p class="card-text">Boylam: ' + earthquake.longitude + '</p>';
        infoHTML += '<p class="card-text">Derinlik: ' + earthquake.depth + ' km</p>';
        infoHTML += '<p class="card-text">Tarih: ' + earthquake.date + '</p>';
        infoHTML += '</div>';
        infoHTML += '</div>';
        infoHTML += '</div>';
      }
  
      infoHTML += '</div>'; // End the Bootstrap row
      $('#info').html(infoHTML);
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