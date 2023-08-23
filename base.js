var map;
var openInfoWindow;

$(document).ready(function(){

  map = new google.maps.Map(document.getElementById('map'), {
    center: {lat: 38.9334, lng: 34.8597},
    zoom: 6 
  });

  function veriGetir(callback){
    $.get('http://127.0.0.1:8000/', function(data){
      callback(data);
    });
  }
  function getAndMarkEarthquakeData() {
    veriGetir(function(data){
      var earthquakes = Object.values(data);
      earthquakes.reverse();

      var tableHTML = '';

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

        tableHTML += '<tr>';
        tableHTML += '<td>' + earthquake.magnitude + '</td>';
        tableHTML += '<td>' + earthquake.location + '</td>';
        tableHTML += '<td>' + earthquake.latitude + '</td>';
        tableHTML += '<td>' + earthquake.longitude + '</td>';
        tableHTML += '<td>' + earthquake.depth + ' km</td>';
        tableHTML += '<td>' + earthquake.date + '</td>';
        tableHTML += '</tr>';
      }

      $('#info tbody').html(tableHTML);

      setTimeout(function () {
        console.log('ınterval')
        getAndMarkEarthquakeData();
      }, 60000); // 60,000 milliseconds = 1 minute
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
