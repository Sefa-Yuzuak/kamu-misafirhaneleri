/* Harita — Leaflet + OpenStreetMap. Tek dosya, üç kullanım:
   1) Tesis sayfası: #harita[data-lat][data-lon]  -> tek iğne
   2) İl sayfası:    #harita[data-il]             -> ilin tesisleri
   3) /harita/:      #harita[data-tum]            -> 562 tesis, kümelenmiş  */
(function () {
  "use strict";
  var kutu = document.getElementById("harita");
  if (!kutu || typeof L === "undefined") return;

  var RENK = { tesis: "#0D5C4E", ilce: "#8F5A15", deniz: "#0B6580" };

  function ignes(renk, kesin) {
    return L.divIcon({
      className: "hi",
      html:
        '<span class="hi-p" style="--p:' + renk + '">' +
        (kesin ? "" : '<span class="hi-y"></span>') +
        "</span>",
      iconSize: [26, 26],
      iconAnchor: [13, 26],
      popupAnchor: [0, -24],
    });
  }

  function balon(t) {
    return (
      '<a class="hb" href="/tesis/' + t.s + '/"><strong>' + t.ad + "</strong>" +
      '<span>' + t.ilce + ", " + t.il + " · " + t.tur + "</span>" +
      (t.kesinlik === "ilce"
        ? '<em>Konum yaklaşıktır (ilçe merkezi)</em>'
        : "") +
      "</a>"
    );
  }

  var katman = L.tileLayer("https://tile.openstreetmap.org/{z}/{x}/{y}.png", {
    maxZoom: 18,
    attribution:
      '&copy; <a href="https://www.openstreetmap.org/copyright" rel="nofollow">OpenStreetMap</a> katkıcıları',
  });

  function kur(merkez, zum) {
    // Dokunmatikte surukleme kapali baslar: harita ekranin buyuk bolumunu
    // kapladigi icin parmak hareketini yutuyor ve sayfa asagi kaydirilamiyordu.
    // Kullanici haritaya dokununca surukleme aciliyor.
    var mobil = L.Browser.mobile;
    var h = L.map(kutu, {
      scrollWheelZoom: false,
      dragging: !mobil,
      tap: true,
      center: merkez,
      zoom: zum,
    });
    katman.addTo(h);
    h.on("click", function () { h.scrollWheelZoom.enable(); });
    h.on("mouseout", function () { h.scrollWheelZoom.disable(); });

    if (mobil) {
      var ipucu = document.createElement("button");
      ipucu.type = "button";
      ipucu.className = "harita-ac";
      ipucu.textContent = "Haritayı etkinleştir";
      var ac = function () {
        h.dragging.enable();
        if (ipucu.parentNode) ipucu.parentNode.removeChild(ipucu);
      };
      ipucu.addEventListener("click", ac);
      kutu.appendChild(ipucu);
    }
    return h;
  }

  // --- 1) tek tesis
  var lat = parseFloat(kutu.dataset.lat);
  var lon = parseFloat(kutu.dataset.lon);
  if (!isNaN(lat) && !isNaN(lon)) {
    var kesin = kutu.dataset.kesinlik === "tesis";
    var h = kur([lat, lon], kesin ? 15 : 12);
    L.marker([lat, lon], { icon: ignes(kesin ? RENK.tesis : RENK.ilce, kesin),
      title: kutu.dataset.ad || "" }).addTo(h);
    if (!kesin) {
      L.circle([lat, lon], { radius: 2500, color: RENK.ilce, weight: 1,
        fillColor: RENK.ilce, fillOpacity: 0.06, dashArray: "4 4" }).addTo(h);
    }
    return;
  }

  // --- 4) rota: numarali duraklar + aralarini birlestiren cizgi
  if (kutu.dataset.rota) {
    var duraklar;
    try { duraklar = JSON.parse(kutu.dataset.rota); } catch (e) { return; }
    if (!duraklar.length) return;
    var hr = kur([duraklar[0].lat, duraklar[0].lon], 8);
    var cizgi = L.polyline(
      duraklar.map(function (d) { return [d.lat, d.lon]; }),
      { color: RENK.tesis, weight: 3, opacity: 0.75, dashArray: "7 6" }
    ).addTo(hr);
    duraklar.forEach(function (d, i) {
      L.marker([d.lat, d.lon], {
        icon: L.divIcon({
          className: "hi",
          html: '<span class="hi-p hi-no" style="--p:' + RENK.tesis + '">' +
                (i + 1) + "</span>",
          iconSize: [28, 28], iconAnchor: [14, 28], popupAnchor: [0, -26],
        }),
        title: (i + 1) + ". " + d.ad,
      })
        .bindPopup('<a class="hb" href="/tesis/' + d.s + '/"><strong>' +
                   (i + 1) + ". " + d.ad + "</strong><span>" + d.yer + "</span></a>")
        .addTo(hr);
    });
    hr.fitBounds(cizgi.getBounds(), { padding: [34, 34], maxZoom: 11 });
    return;
  }

  // --- 2 ve 3) çoklu
  var il = kutu.dataset.il || "";
  var tum = kutu.dataset.tum === "1";
  if (!il && !tum) return;

  fetch("/data/harita.json")
    .then(function (r) { return r.json(); })
    .then(function (d) {
      var kayitlar = d.t
        .map(function (x) {
          return { lat: x[0], lon: x[1], ad: x[2], s: x[3], il: x[4], ilce: x[5],
                   tur: d.turler[x[6]], dz: x[7], kesinlik: x[8] ? "tesis" : "ilce" };
        })
        .filter(function (t) { return tum || t.il === il; });
      if (!kayitlar.length) { kutu.remove(); return; }

      var h = kur([39.2, 35.2], 6);
      var grup = tum && L.markerClusterGroup
        ? L.markerClusterGroup({ maxClusterRadius: 48, showCoverageOnHover: false })
        : L.featureGroup();

      kayitlar.forEach(function (t) {
        var renk = t.dz ? RENK.deniz : t.kesinlik === "tesis" ? RENK.tesis : RENK.ilce;
        L.marker([t.lat, t.lon], { icon: ignes(renk, t.kesinlik === "tesis"), title: t.ad })
          .bindPopup(balon(t))
          .addTo(grup);
      });
      h.addLayer(grup);

      var sinir = (grup.getBounds && grup.getBounds()) || null;
      if (sinir && sinir.isValid()) h.fitBounds(sinir, { padding: [30, 30], maxZoom: 13 });

      var say = document.getElementById("harita-say");
      if (say) say.textContent = kayitlar.length + " tesis haritada";
    })
    .catch(function () { kutu.remove(); });
})();
