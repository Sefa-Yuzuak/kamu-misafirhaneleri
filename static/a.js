/* Arama: /data/ara.json bir kez çekilir, gerisi tarayıcıda. */
(function () {
  "use strict";

  var HARF = { ç: "c", ğ: "g", ı: "i", ö: "o", ş: "s", ü: "u", â: "a", î: "i", û: "u" };
  function sade(s) {
    return String(s).toLowerCase().replace(/[çğıöşüâîû]/g, function (h) {
      return HARF[h] || h;
    });
  }

  var kutu = document.getElementById("q");
  if (!kutu) return;
  var panel = document.getElementById("oneri");
  var veri = null, yukleniyor = false, secili = -1;

  function yukle() {
    if (veri || yukleniyor) return Promise.resolve(veri);
    yukleniyor = true;
    return fetch("/data/ara.json")
      .then(function (r) { return r.json(); })
      .then(function (d) {
        veri = d.t.map(function (x) {
          return { ad: x[0], ilce: x[1], il: x[2], s: x[3], tur: d.turler[x[4]], dz: x[5],
                   k: sade(x[0] + " " + x[1] + " " + x[2]) };
        });
        yukleniyor = false;
        return veri;
      })
      .catch(function () { yukleniyor = false; return null; });
  }

  function bul(sorgu, adet) {
    var q = sade(sorgu).trim();
    if (!q || !veri) return [];
    var kelimeler = q.split(/\s+/);
    var sonuc = [];
    for (var i = 0; i < veri.length && sonuc.length < adet * 4; i++) {
      var t = veri[i], uyar = true, puan = 0;
      for (var j = 0; j < kelimeler.length; j++) {
        var p = t.k.indexOf(kelimeler[j]);
        if (p < 0) { uyar = false; break; }
        puan += p === 0 ? 0 : p < 20 ? 5 : 20;
      }
      if (uyar) sonuc.push({ t: t, p: puan });
    }
    sonuc.sort(function (a, b) { return a.p - b.p; });
    return sonuc.slice(0, adet).map(function (x) { return x.t; });
  }

  function ikonu(t) {
    return '<svg class="ik" viewBox="0 0 24 24" aria-hidden="true"><path d="' +
      (t.dz
        ? "M2 17.2c1.7 0 1.7 1.6 3.3 1.6s1.7-1.6 3.4-1.6 1.7 1.6 3.3 1.6 1.7-1.6 3.3-1.6 1.7 1.6 3.4 1.6 1.6-1.6 3.3-1.6M2 12.4c1.7 0 1.7 1.6 3.3 1.6s1.7-1.6 3.4-1.6 1.7 1.6 3.3 1.6 1.7-1.6 3.3-1.6 1.7 1.6 3.4 1.6 1.6-1.6 3.3-1.6"
        : "M20 10.4c0 5.2-6.6 10.3-7.6 11a.7.7 0 0 1-.8 0C10.6 20.7 4 15.6 4 10.4a8 8 0 0 1 16 0ZM14.7 10.3a2.7 2.7 0 1 1-5.4 0 2.7 2.7 0 0 1 5.4 0Z") +
      '"/></svg>';
  }

  function ciz(liste) {
    if (!liste.length) { panel.innerHTML = ""; kutu.setAttribute("aria-expanded", "false"); return; }
    panel.innerHTML = liste.map(function (t) {
      return '<a href="/tesis/' + t.s + '/" role="option">' + ikonu(t) +
        '<span><span class="o-ad">' + t.ad + '</span><br>' +
        '<span class="o-yer">' + t.ilce + ", " + t.il + " · " + t.tur + "</span></span></a>";
    }).join("");
    kutu.setAttribute("aria-expanded", "true");
    secili = -1;
  }

  var zaman;
  function calistir() {
    clearTimeout(zaman);
    zaman = setTimeout(function () {
      yukle().then(function () { ciz(bul(kutu.value, 8)); });
    }, 80);
  }

  kutu.addEventListener("focus", yukle);
  kutu.addEventListener("input", calistir);
  kutu.addEventListener("keydown", function (ev) {
    var ogeler = panel.querySelectorAll("a");
    if (ev.key === "ArrowDown" || ev.key === "ArrowUp") {
      if (!ogeler.length) return;
      ev.preventDefault();
      if (secili >= 0) ogeler[secili].classList.remove("sec");
      secili = ev.key === "ArrowDown"
        ? (secili + 1) % ogeler.length
        : (secili - 1 + ogeler.length) % ogeler.length;
      ogeler[secili].classList.add("sec");
      ogeler[secili].scrollIntoView({ block: "nearest" });
    } else if (ev.key === "Enter") {
      if (secili >= 0 && ogeler[secili]) { ev.preventDefault(); ogeler[secili].click(); }
    } else if (ev.key === "Escape") {
      panel.innerHTML = ""; kutu.setAttribute("aria-expanded", "false"); kutu.blur();
    }
  });
  document.addEventListener("click", function (ev) {
    if (!ev.target.closest(".ara")) { panel.innerHTML = ""; kutu.setAttribute("aria-expanded", "false"); }
  });
  document.addEventListener("keydown", function (ev) {
    if (ev.key === "/" && document.activeElement !== kutu &&
        !/^(INPUT|TEXTAREA|SELECT)$/.test(document.activeElement.tagName)) {
      ev.preventDefault(); kutu.focus();
    }
  });

  // /ara/ sayfası: adres çubuğundaki ?q= ile tam sonuç listesi
  var liste = document.getElementById("sonuclar");
  if (liste) {
    var q = new URLSearchParams(location.search).get("q") || "";
    kutu.value = q;
    var basim = function () {
      var s = bul(kutu.value, 60);
      document.getElementById("sonuc-say").textContent =
        kutu.value.trim() ? s.length + " sonuç" : "";
      liste.innerHTML = s.length
        ? s.map(function (t) {
            return '<a class="sonuc" href="/tesis/' + t.s + '/">' +
              '<strong>' + t.ad + "</strong><span>" + t.ilce + ", " + t.il +
              " · " + t.tur + "</span></a>";
          }).join("")
        : (kutu.value.trim() ? '<p class="bos">Eşleşen tesis bulunamadı.</p>' : "");
    };
    yukle().then(basim);
    kutu.addEventListener("input", function () {
      clearTimeout(zaman);
      zaman = setTimeout(function () {
        yukle().then(basim);
        history.replaceState(null, "", kutu.value ? "?q=" + encodeURIComponent(kutu.value) : "/ara/");
      }, 120);
    });
  }
})();
