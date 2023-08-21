var map;
var openInfoWindow;

$(document).ready(function(){

  map = new google.maps.Map(document.getElementById('map'), {
    center: {lat: 38.9334, lng: 34.8597},
    zoom: 6 
  });

  function veriGetir(callback){
    $.get('http://127.0.0.1:8001/', function(data){
      callback(data);
    });
  }

  function getAndMarkEarthquakeData() {
    veriGetir(function(data){
      var earthquakes = Object.values(data);
      earthquakes.reverse();

      var infoHTML = '<div class="row">';

      for (var i = 0; i < earthquakes.length; i++) {
        var earthquake = earthquakes[i];
        var latLng = new google.maps.LatLng(parseFloat(earthquake.latitude), parseFloat(earthquake.longitude));

        var markerColor = (i === 0) ? 'red' : 'blue';

        var marker = new google.maps.Marker({
          position: latLng,
          map: map,
          title: earthquake.location,
          icon: {
            path: google.maps.SymbolPath.CIRCLE,
            fillColor: markerColor,
            fillOpacity: 0.7,
            strokeWeight: 0,
            scale: 10
          }
        });

        var contentString = "Yer: " + earthquake.location +
         "<br>Enlem: " + earthquake.latitude +
         "<br>Boylam: " + earthquake.longitude +
         "<br>Derinlik: " + earthquake.depth + " km"+ 
         "<br>Büyüklük: " + earthquake.magnitude +
         "<br>Tarih: " + earthquake.date;

        attachInfoWindow(marker, contentString);

        infoHTML += '<div class="col-md-2 mb-2">';
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

      infoHTML += '</div>';
      $('#info').html(infoHTML);
    });
  }

  function attachInfoWindow(marker, content) {
    var infoWindow = new google.maps.InfoWindow({
      content: content
    });

    marker.addListener('click', function() {
      if (openInfoWindow) {
        openInfoWindow.close();
      }
      
      infoWindow.open(marker.get('map'), marker);
      openInfoWindow = infoWindow;
    });
  }

  getAndMarkEarthquakeData();
});
