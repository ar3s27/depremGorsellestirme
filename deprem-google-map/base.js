var earthquake_data = "earthquake_data.json"; // Deprem verilerinin bulunduğu JSON dosyasının adı

var map; // Google Haritalar nesnesi
var openInfoWindow; // Şu an açık olan bilgi penceresi

$(document).ready(function(){

  // Haritayı oluşturma
  map = new google.maps.Map(document.getElementById('map'), {
    center: {lat: 38.9334, lng: 34.8597}, // Haritanın merkezi koordinatları
    zoom: 6 
  });

  // Deprem verilerini çekme ve işaretleme işlevi
  function getAndMarkEarthquakeData() {
    // JSON dosyasını al
    $.getJSON(earthquake_data, function(data) {
      var earthquakes = Object.values(data); // JSON verilerini diziye çevir
      earthquakes.reverse(); // Depremleri ters çevir, en yeni en üstte olsun

      var infoHTML = '<div class="row">'; // Bootstrap satırını başlat

      for (var i = 0; i < earthquakes.length; i++) {
        var earthquake = earthquakes[i];
        var latLng = new google.maps.LatLng(parseFloat(earthquake.latitude), parseFloat(earthquake.longitude));

        var markerColor = (i === 0) ? 'red' : 'blue'; // En son depremin işaret rengini belirle
        
        // Yeni bir işaretçi oluştur
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

        // Bilgi penceresi içeriği oluşturma
        var contentString = "Yer: " + earthquake.location +
         "<br>Enlem: " + earthquake.latitude +
         "<br>Boylam: " + earthquake.longitude +
         "<br>Derinlik: " + earthquake.depth + " km"+ 
         "<br>Büyüklük: " + earthquake.magnitude +
         "<br>Tarih: " + earthquake.date;

        // İşaretçiye bilgi penceresi ekleniyor
        attachInfoWindow(marker, contentString);

        // Bootstrap kartları oluşturma
        infoHTML += '<div class="col-md-2 mb-2">'; // Bootstrap sütunu oluştur
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

      infoHTML += '</div>'; // Bootstrap satırını kapat
      $('#info').html(infoHTML); // HTML içeriğini güncelle
    });
  }

  // İşaretçiye tıklanınca bilgi penceresini gösterme işlevi
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

  // Deprem verilerini çek ve işaretle
  getAndMarkEarthquakeData();
});