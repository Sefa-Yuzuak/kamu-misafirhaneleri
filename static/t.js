/* Hesaplama araçları. Tek veri dosyası (/data/tesis-tam.json), hepsi tarayıcıda.
   Sunucuya hiçbir şey gönderilmez. */
(function () {
  "use strict";

  var SAPMA = 1.27, HIZ = 78;
  var HARF = { ç: "c", ğ: "g", ı: "i", ö: "o", ş: "s", ü: "u", â: "a", î: "i", û: "u" };
  function sade(s) {
    return String(s).toLowerCase().replace(/[çğıöşüâîû]/g, function (h) { return HARF[h] || h; });
  }
  function tl(n) {
    return new Intl.NumberFormat("tr-TR", { maximumFractionDigits: 0 }).format(Math.round(n)) + " TL";
  }
  function sayi(n) { return new Intl.NumberFormat("tr-TR").format(n); }

  function km(a, b) {
    var R = 6371, r = Math.PI / 180;
    var dLat = (b[0] - a[0]) * r, dLon = (b[1] - a[1]) * r;
    var h = Math.sin(dLat / 2) * Math.sin(dLat / 2) +
      Math.cos(a[0] * r) * Math.cos(b[0] * r) * Math.sin(dLon / 2) * Math.sin(dLon / 2);
    return Math.round(R * 2 * Math.asin(Math.sqrt(h)) * SAPMA / 5) * 5;
  }
  function sureMetni(k) {
    var s = Math.round(k / HIZ * 2) / 2, t = Math.floor(s), d = Math.round((s - t) * 60);
    return s < 1 ? Math.round(s * 60) + " dk" : t + " sa" + (d ? " " + d + " dk" : "");
  }

  var D = null;
  function veri() {
    if (D) return Promise.resolve(D);
    return fetch("/data/tesis-tam.json").then(function (r) { return r.json(); }).then(function (d) {
      D = {
        iller: d.iller,
        t: d.t.map(function (x) {
          return { s: x[0], ad: x[1], il: x[2], ilce: x[3], tur: d.turler[x[4]],
                   k: [x[5], x[6]], dz: x[7], hv: x[8], fiyat: x[9], fs: x[10],
                   tel: x[11], ol: x[12], anahtar: sade(x[1] + " " + x[3] + " " + x[2]) };
        }),
      };
      return D;
    });
  }

  function el(id) { return document.getElementById(id); }
  function esc(s) {
    return String(s == null ? "" : s).replace(/[&<>"]/g, function (c) {
      return { "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" }[c];
    });
  }

  /* --- tesis seçici: metin kutusu + öneri listesi --------------------- */
  function secici(girdiId, oneriId, secildi) {
    var g = el(girdiId), o = el(oneriId);
    if (!g || !o) return null;
    var durum = { tesis: null };
    function kapat() { o.innerHTML = ""; g.setAttribute("aria-expanded", "false"); }
    function ciz() {
      var q = sade(g.value.trim());
      if (!q || !D) return kapat();
      var bulunan = D.t.filter(function (t) { return t.anahtar.indexOf(q) >= 0; }).slice(0, 8);
      if (!bulunan.length) return kapat();
      o.innerHTML = bulunan.map(function (t, i) {
        return '<a href="#" data-i="' + i + '" role="option"><span>' +
          '<span class="o-ad">' + esc(t.ad) + "</span><br>" +
          '<span class="o-yer">' + esc(t.ilce) + ", " + esc(t.il) + " · " + esc(t.tur) +
          "</span></span></a>";
      }).join("");
      g.setAttribute("aria-expanded", "true");
      Array.prototype.forEach.call(o.querySelectorAll("a"), function (a, i) {
        a.addEventListener("click", function (ev) {
          ev.preventDefault();
          durum.tesis = bulunan[i];
          g.value = bulunan[i].ad;
          kapat();
          secildi(bulunan[i]);
        });
      });
    }
    g.addEventListener("input", function () {
      durum.tesis = null;
      veri().then(ciz);
      secildi(null);
    });
    g.addEventListener("focus", function () { veri().then(ciz); });
    g.addEventListener("blur", function () { setTimeout(kapat, 180); });
    return durum;
  }

  function say(v, varsayilan) {
    var n = parseFloat(v);
    return isFinite(n) && n >= 0 ? n : varsayilan;
  }

  /* --- 1) Bana en yakın ---------------------------------------------- */
  if (el("a-sonuc")) {
    var alanlar = ["a-il", "a-tur", "a-adet", "a-deniz", "a-havuz", "a-fiyat"];
    var calistirEnYakin = function () {
      var il = el("a-il").value, nokta = D.iller[il];
      if (!nokta) return;
      var tur = el("a-tur").value, adet = parseInt(el("a-adet").value, 10) || 25;
      var liste = D.t.filter(function (t) {
        if (tur && t.tur !== tur) return false;
        if (el("a-deniz").checked && !t.dz) return false;
        if (el("a-havuz").checked && !t.hv) return false;
        if (el("a-fiyat").checked && !t.fiyat) return false;
        return true;
      }).map(function (t) {
        return { t: t, d: km(nokta, t.k) };
      }).sort(function (x, y) { return x.d - y.d; }).slice(0, adet);

      el("a-ozet").textContent = liste.length
        ? il + " merkezinden en yakın " + liste.length + " tesis · en yakını " +
          liste[0].d + " km (" + liste[0].t.ad + ")"
        : "Seçtiğiniz süzgeçlere uyan tesis yok.";

      el("a-sonuc").innerHTML = liste.map(function (x) {
        var t = x.t;
        return '<a class="yakin-k" href="/tesis/' + t.s + '/">' +
          '<span class="yakin-km">' + x.d + '<small>km</small></span>' +
          '<span class="yakin-ad"><strong>' + esc(t.ad) + "</strong>" +
          "<span>" + esc(t.ilce) + ", " + esc(t.il) + " · " + esc(t.tur) +
          (t.dz ? " · denize yakın" : "") + (t.hv ? " · havuzlu" : "") + "</span>" +
          (t.fiyat ? '<span class="yakin-fiyat">' + esc(t.fiyat) + "</span>" : "") +
          "</span><span class='yakin-sure'>" + sureMetni(x.d) + "</span></a>";
      }).join("");
    };
    veri().then(function () {
      alanlar.forEach(function (id) {
        var e2 = el(id);
        if (e2) e2.addEventListener("change", calistirEnYakin);
      });
      calistirEnYakin();
    });
  }

  /* --- 2) Tatil bütçesi ----------------------------------------------- */
  if (el("b-sonuc")) {
    var bTesis = null;
    var hesapla = function () {
      var gece = say(el("b-gece").value, 4);
      var yetiskin = say(el("b-yetiskin").value, 2);
      var cocuk = say(el("b-cocuk").value, 0);
      var kisi = yetiskin + cocuk;
      var oda = say(el("b-oda").value, 0);
      var tuketim = say(el("b-tuketim").value, 7);
      var yakitFiyat = say(el("b-yakit").value, 50);
      var gunluk = say(el("b-harcama").value, 0);
      var otel = say(el("b-otel").value, 0);

      var mesafe = 0, il = el("b-il").value;
      if (bTesis && D.iller[il]) mesafe = km(D.iller[il], bTesis.k);

      var konaklama = oda * gece;
      var yakit = mesafe * 2 * (tuketim / 100) * yakitFiyat;
      var harcama = gunluk * kisi * (gece + 1);
      var toplam = konaklama + yakit + harcama;
      var otelToplam = otel * gece;
      var fark = otelToplam - konaklama;

      var satir = function (ad, tutar, not) {
        return '<div class="hs-satir"><span>' + ad +
          (not ? '<small>' + not + "</small>" : "") + "</span><b>" + tl(tutar) + "</b></div>";
      };
      el("b-sonuc").innerHTML =
        '<div class="hs-kutu">' +
        satir("Konaklama", konaklama, gece + " gece × " + tl(oda)) +
        satir("Yakıt (gidiş-dönüş)", yakit,
          mesafe ? sayi(mesafe * 2) + " km × " + tuketim + " L/100km × " + tl(yakitFiyat)
                 : "tesis seçilmedi") +
        satir("Yeme-içme ve harcama", harcama,
          kisi + " kişi × " + (gece + 1) + " gün × " + tl(gunluk)) +
        '<div class="hs-satir hs-toplam"><span>Toplam</span><b>' + tl(toplam) + "</b></div>" +
        '<div class="hs-alt">' +
          "<span>Kişi başı <b>" + tl(kisi ? toplam / kisi : 0) + "</b></span>" +
          "<span>Gece başı <b>" + tl(gece ? toplam / gece : 0) + "</b></span>" +
        "</div></div>" +
        (otel > 0
          ? '<div class="hs-kutu hs-kiyas' + (fark > 0 ? " hs-iyi" : "") + '">' +
            "<p>Aynı " + gece + " gece ticari bir otelde <b>" + tl(otelToplam) +
            "</b> tutardı. Kamu tesisi konaklaması <b>" + tl(Math.abs(fark)) + "</b> " +
            (fark >= 0 ? "daha ucuz" : "daha pahalı") +
            (otelToplam > 0 ? " (%" + Math.round(Math.abs(fark) / otelToplam * 100) + ")" : "") +
            ". Yol ve yemek her iki durumda da aynı olduğu için farka katılmadı.</p></div>"
          : "");
    };
    var bSec = secici("b-tesis", "b-oneri", function (t) {
      bTesis = t;
      var not = el("b-oda-not");
      if (t && t.fs) {
        el("b-oda").value = t.fs;
        not.textContent = "Tesisin yayımladığı fiyattan dolduruldu";
      } else if (t) {
        not.textContent = "Bu tesis fiyat yayımlamamış — kendi aldığınız fiyatı yazın";
      } else {
        not.textContent = "";
      }
      hesapla();
    });
    veri().then(function () {
      ["b-il", "b-gece", "b-yetiskin", "b-cocuk", "b-oda", "b-tuketim", "b-yakit",
       "b-harcama", "b-otel"].forEach(function (id) {
        var e2 = el(id);
        if (e2) e2.addEventListener("input", hesapla);
      });
      hesapla();
    });
  }

  /* --- 3) Mesafe ------------------------------------------------------ */
  if (el("m-sonuc")) {
    var mTesis = null;
    var mHesap = function () {
      var il = el("m-il").value;
      if (!mTesis || !D.iller[il]) {
        el("m-sonuc").innerHTML =
          '<p class="hs-bos">Bir tesis seçin; mesafe, süre ve yakıt maliyeti burada çıkacak.</p>';
        return;
      }
      var d = km(D.iller[il], mTesis.k);
      var tuketim = say(el("m-tuketim").value, 7), fiyat = say(el("m-yakit").value, 50);
      var yakit = d * (tuketim / 100) * fiyat;
      el("m-sonuc").innerHTML =
        '<div class="hs-kutu"><div class="hs-buyuk">' +
        '<span><b>' + sayi(d) + "</b><small>km tek yön</small></span>" +
        '<span><b>' + sureMetni(d) + "</b><small>tahmini sürüş</small></span>" +
        '<span><b>' + tl(yakit) + "</b><small>yakıt, tek yön</small></span>" +
        '<span><b>' + tl(yakit * 2) + "</b><small>gidiş-dönüş</small></span></div>" +
        "<p class='hs-not'>" + esc(il) + " → " + esc(mTesis.ad) + " (" +
        esc(mTesis.ilce) + ", " + esc(mTesis.il) + "). " +
        '<a href="/tesis/' + mTesis.s + '/">Tesis sayfası</a></p></div>';
    };
    secici("m-tesis", "m-oneri", function (t) { mTesis = t; mHesap(); });
    veri().then(function () {
      ["m-il", "m-tuketim", "m-yakit"].forEach(function (id) {
        var e2 = el(id);
        if (e2) e2.addEventListener("input", mHesap);
      });
      mHesap();
    });
  }

  /* --- 4) Karşılaştırma ------------------------------------------------ */
  if (el("k-sonuc")) {
    var secim = [null, null, null];
    var kCiz = function () {
      var v = secim.filter(Boolean);
      if (v.length < 2) {
        el("k-sonuc").innerHTML =
          '<p class="hs-bos">Karşılaştırmak için en az iki tesis seçin.</p>';
        return;
      }
      var satirlar = [
        ["Konum", function (t) { return esc(t.ilce) + ", " + esc(t.il); }],
        ["Tür", function (t) { return esc(t.tur); }],
        ["Yayımlanmış fiyat", function (t) { return t.fiyat ? esc(t.fiyat) : "—"; }],
        ["Denize konumu", function (t) { return t.dz ? esc(t.dz) : "—"; }],
        ["Olanaklar", function (t) { return t.ol ? esc(t.ol) : "—"; }],
        ["Ankara'dan", function (t) {
          var d = km(D.iller["Ankara"], t.k); return sayi(d) + " km · " + sureMetni(d);
        }],
        ["Telefon", function (t) {
          return t.tel ? '<a href="tel:+9' + t.tel.replace(/\D/g, "").replace(/^0/, "") +
            '">' + esc(t.tel) + "</a>" : "—";
        }],
        ["", function (t) { return '<a class="dg dg-1 dg-sm" href="/tesis/' + t.s + '/">Sayfası</a>'; }],
      ];
      el("k-sonuc").innerHTML =
        '<div class="yazi"><table><thead><tr><th></th>' +
        v.map(function (t) { return "<th>" + esc(t.ad) + "</th>"; }).join("") +
        "</tr></thead><tbody>" +
        satirlar.map(function (s) {
          return "<tr><th>" + s[0] + "</th>" +
            v.map(function (t) { return "<td>" + s[1](t) + "</td>"; }).join("") + "</tr>";
        }).join("") +
        "</tbody></table></div>";
    };
    [1, 2, 3].forEach(function (n) {
      secici("k-" + n, "k-" + n + "-oneri", function (t) { secim[n - 1] = t; kCiz(); });
    });
    veri().then(kCiz);
  }
})();
