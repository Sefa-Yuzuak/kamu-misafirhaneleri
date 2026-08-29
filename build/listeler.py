"""Sıralı liste sayfaları — "Ankara'ya en yakın deniz tesisleri" gibi.

Üretken arama motorlarının en çok alıntıladığı biçim sıralı, gerekçeli ve
sayı içeren listelerdir. Buradaki her liste kendi veri kümemizden süzülür;
sıralama ölçütü sayfada açıkça yazılıdır ve elle seçim yapılmaz.
"""

from __future__ import annotations

from parca import AD, SITE, e, ik, kabuk
from mesafe import CIKIS_NOKTALARI, karayolu_km, sure_metni, sure_saat
from veri import TURLER, fiyat_taban, kisa_ad, slug, tesis_slug, yonelme


def _havuzlu(t: dict) -> bool:
    return any("havuz" in o.lower() for o in t.get("olanaklar") or [])


def _fiyat_sayisi(t: dict) -> int | None:
    """Sıralama için yayımlanan en düşük tutar."""
    n = fiyat_taban(t.get("fiyat_2026"))
    return n or None


def _mesafe(t: dict, konumlar: dict, nokta: tuple[float, float]) -> int | None:
    k = konumlar.get(tesis_slug(t))
    return karayolu_km(nokta, (k["lat"], k["lon"])) if k else None


# --------------------------------------------------------------------------
# Liste tanımları
# --------------------------------------------------------------------------
# anahtar -> (başlık, ikon, ölçüt cümlesi, süzgeç, sıralama, sütunlar)


def liste_tanimlari(konumlar: dict) -> dict:
    sehirler = {ad: (la, lo) for ad, la, lo in CIKIS_NOKTALARI}

    def yakin_deniz(sehir: str):
        n = sehirler[sehir]
        return {
            "baslik": f"{yonelme(sehir)} en yakın sahil kamu tesisleri",
            "ikon": "deniz",
            "olcut": (
                "Denize konumu tesisin kendi yayınından doğrulanmış tesisler, "
                f"{yonelme(sehir)} tahmini karayolu mesafesine göre en yakından "
                "uzağa sıralandı."
            ),
            "suzgec": lambda t: bool(t.get("deniz")) and tesis_slug(t) in konumlar,
            "sira": lambda t: _mesafe(t, konumlar, n) or 9999,
            "sehir": sehir,
            "sutunlar": ["mesafe", "sure", "deniz", "fiyat"],
            "adet": 30,
        }

    return {
        "ankaraya-en-yakin-deniz-tesisleri": yakin_deniz("Ankara"),
        "istanbula-en-yakin-deniz-tesisleri": yakin_deniz("İstanbul"),
        "izmire-en-yakin-deniz-tesisleri": yakin_deniz("İzmir"),
        "havuzlu-kamu-tesisleri": {
            "baslik": "Havuzu olan kamu misafirhaneleri",
            "ikon": "havuz",
            "olcut": "Tesisin kendi tanıtımında havuzu geçen tesisler. Küçük çocukla "
            "gidenler için denizden çoğu zaman daha kullanışlı olduğundan ayrı "
            "liste yapıldı. Ankara'ya uzaklığa göre sıralı.",
            "suzgec": _havuzlu,
            "sira": lambda t: _mesafe(t, konumlar, sehirler["Ankara"]) or 9999,
            "sehir": "Ankara",
            "sutunlar": ["mesafe", "olanak", "deniz", "fiyat"],
            "adet": 40,
        },
        "en-ucuz-kamu-misafirhaneleri": {
            "baslik": "Yayımlanmış fiyatı en düşük kamu misafirhaneleri",
            "ikon": "para",
            "olcut": "Yalnızca tesisin kendisi fiyat yayımlamışsa listeye girer. "
            "Sıralama, yayımlanan metindeki en düşük tutara göredir — yani "
            "\"şu fiyattan başlıyor\" anlamına gelir. Bazı tesisler oda "
            "başına, bazıları kişi başına fiyat açıklıyor; karşılaştırmadan "
            "önce tablodaki fiyat metnini okuyun. Tahmini fiyat yazılmaz.",
            "suzgec": lambda t: _fiyat_sayisi(t) is not None,
            "sira": lambda t: _fiyat_sayisi(t) or 999999,
            "sehir": "Ankara",
            "sutunlar": ["fiyat", "mesafe", "deniz"],
            "adet": 40,
        },
        "cocuklu-aileler-icin-kamu-tesisleri": {
            "baslik": "Çocuklu aileler için kamu tesisleri",
            "ikon": "cocuk",
            "olcut": "Havuzu olan ya da denize yakın konumu doğrulanmış tesisler. "
            "Havuzlular önce gelir, sonra Ankara'ya uzaklığa göre sıralanır — "
            "küçük çocukla uzun yol tek başına belirleyici olduğu için.",
            "suzgec": lambda t: (_havuzlu(t) or bool(t.get("deniz")))
            and tesis_slug(t) in konumlar,
            "sira": lambda t: (
                0 if _havuzlu(t) else 1,
                _mesafe(t, konumlar, sehirler["Ankara"]) or 9999,
            ),
            "sehir": "Ankara",
            "sutunlar": ["mesafe", "olanak", "deniz", "fiyat"],
            "adet": 40,
        },
        "universite-sosyal-tesisleri": {
            "baslik": "Üniversite sosyal tesisleri ve misafirhaneleri",
            "ikon": "bina",
            "olcut": "Üniversitelere bağlı konaklama tesisleri. Çoğu kıyıda ve "
            "yalnızca yaz döneminde açık; kontenjan üniversitenin kendi "
            "yönergesine göre belirlenir. Ankara'ya uzaklığa göre sıralı.",
            "suzgec": lambda t: t["tur"] == "Üniversite Misafirhanesi",
            "sira": lambda t: _mesafe(t, konumlar, sehirler["Ankara"]) or 9999,
            "sehir": "Ankara",
            "sutunlar": ["mesafe", "kurum", "deniz", "fiyat"],
            "adet": 40,
        },
    }


# --------------------------------------------------------------------------
_SUTUN_BASLIK = {
    "mesafe": "Mesafe",
    "sure": "Süre",
    "deniz": "Denize konumu",
    "fiyat": "Yayımlanmış fiyat",
    "olanak": "Olanaklar",
    "kurum": "Bağlı kurum",
}


def _hucre(sutun: str, t: dict, km: int | None) -> str:
    if sutun == "mesafe":
        return f"<strong>{km} km</strong>" if km is not None else "—"
    if sutun == "sure":
        return sure_metni(sure_saat(km)) if km is not None else "—"
    if sutun == "deniz":
        return e(t.get("deniz") or "—")
    if sutun == "fiyat":
        return e(t.get("fiyat_2026") or "—")
    if sutun == "olanak":
        return e(", ".join(t.get("olanaklar") or []) or "—")
    if sutun == "kurum":
        return e(t.get("kurum") or "—")
    return "—"


def liste_sayfasi(anahtar: str, tanim: dict, tesisler: list[dict],
                  konumlar: dict) -> str:
    from uret import kirinti_ld, sss_html, sss_ld

    yol = f"/liste/{anahtar}/"
    sehir = tanim["sehir"]
    nokta = next((la, lo) for ad, la, lo in CIKIS_NOKTALARI if ad == sehir)

    secilen = sorted([t for t in tesisler if tanim["suzgec"](t)], key=tanim["sira"])
    tamami = len(secilen)
    secilen = secilen[: tanim["adet"]]
    if not secilen:
        return ""

    basliklar = "".join(f"<th>{_SUTUN_BASLIK[s]}</th>" for s in tanim["sutunlar"])
    satirlar = ""
    for i, t in enumerate(secilen, 1):
        km = _mesafe(t, konumlar, nokta)
        hucreler = "".join(_hucre(s, t, km) for s in tanim["sutunlar"])
        hucreler = "".join(f"<td>{_hucre(s, t, km)}</td>" for s in tanim["sutunlar"])
        satirlar += (
            f'<tr><td>{i}</td>'
            f'<td><a href="/tesis/{tesis_slug(t)}/">{e(kisa_ad(t["ad"]))}</a><br>'
            f'<small style="color:var(--soluk)">{e(t["ilce"])}, {e(t["il"])}</small></td>'
            f"{hucreler}</tr>"
        )

    ilk = secilen[0]
    ilk_km = _mesafe(ilk, konumlar, nokta)
    iller = sorted({t["il"] for t in secilen})

    ozet = (
        f"Bu listede <strong>{len(secilen)} tesis</strong> var"
        + (f" (ölçüte uyan toplam {tamami} tesisten ilk {len(secilen)} tanesi)"
           if tamami > len(secilen) else "")
        + f". {tanim['olcut']} Listedeki tesisler {len(iller)} ile yayılmış durumda. "
        f"İlk sırada <strong>{kisa_ad(ilk['ad'])}</strong> "
        + (f"({ilk['ilce']}, {ilk['il']} — {yonelme(sehir)} yaklaşık {ilk_km} km) "
           if ilk_km else f"({ilk['ilce']}, {ilk['il']}) ")
        + "yer alıyor."
    )

    sss = [
        (f"{tanim['baslik']} nasıl sıralandı?",
         tanim["olcut"] + " Elle seçim veya öne çıkarma yapılmadı; liste her "
         "derlemede aynı ölçütle yeniden üretilir."),
        ("Listedeki tesislerde rezervasyon nasıl yapılır?",
         "Rezervasyon her tesisin kendi telefonundan yapılır; merkezî bir sistem "
         "yoktur. Tesis adına tıklayarak telefon numarasına, yol tarifine ve "
         "yayımlanmış fiyata ulaşabilirsiniz."),
    ]
    if any(t.get("fiyat_2026") for t in secilen):
        sss.append(
            ("Listedeki fiyatlar güncel mi?",
             "Fiyatlar tesislerin kendi yayımladığı 2026 listelerinden alınmıştır ve "
             "yıl içinde değişebilir. Bu sitede tahmini fiyat yazılmaz; ödeme öncesi "
             "tesisi arayıp teyit edin."),
        )

    kirintilar = [("/", "Ana sayfa"), ("/liste/", "Listeler"), (yol, tanim["baslik"])]
    icerik = f"""<section class="bl kap" style="max-width:1000px">
<span class="rz rz-vurgu">{ik(tanim["ikon"])}Sıralı liste</span>
<h1 style="margin-top:10px">{e(tanim["baslik"])}</h1>
<p class="ozet" style="margin-top:18px">{ozet}</p>
<div class="yazi" style="margin-top:24px"><table>
<thead><tr><th>#</th><th>Tesis</th>{basliklar}</tr></thead>
<tbody>{satirlar}</tbody></table></div>
<div class="not" style="margin-top:18px">{ik("bilgi")}<div>
Mesafeler koordinatlardan hesaplanan tahminlerdir, ölçülmüş değildir.
Kendi ilinizden mesafeyi görmek için
<a href="/araclar/en-yakin/">en yakın tesis aracını</a> kullanın.</div></div>
</section>
<section class="bl kap bl-cizgi" style="max-width:1000px">
<h2>Sık sorulan sorular</h2>{sss_html(sss)}</section>"""

    ld_liste = {
        "@context": "https://schema.org",
        "@type": "ItemList",
        "name": tanim["baslik"],
        "description": tanim["olcut"],
        "numberOfItems": len(secilen),
        "itemListOrder": "https://schema.org/ItemListOrderAscending",
        "itemListElement": [
            {
                "@type": "ListItem",
                "position": i,
                "url": f"{SITE}/tesis/{tesis_slug(t)}/",
                "name": kisa_ad(t["ad"]),
            }
            for i, t in enumerate(secilen, 1)
        ],
    }
    return kabuk(
        baslik=f"{tanim['baslik']} ({len(secilen)} tesis)",
        aciklama=(f"{tanim['baslik']} — {len(secilen)} tesis, mesafe ve fiyatlarıyla "
                  f"sıralı liste. İlk sırada {kisa_ad(ilk['ad'])}.")[:158],
        yol=yol,
        icerik=icerik,
        kirintilar=kirintilar,
        aktif="/liste/",
        jsonld=[ld_liste, sss_ld(sss), kirinti_ld(kirintilar)],
    )


def listeler_dizini(tanimlar: dict, tesisler: list[dict], konumlar: dict) -> str:
    from uret import kirinti_ld

    kartlar = ""
    for anahtar, tanim in tanimlar.items():
        adet = len([t for t in tesisler if tanim["suzgec"](t)])
        if not adet:
            continue
        kartlar += f"""<a class="tur-k" href="/liste/{anahtar}/">
{ik(tanim["ikon"], "ik tur-ik")}<strong>{e(tanim["baslik"])}</strong>
<span>{min(adet, tanim["adet"])} tesis</span>
<em>{e(tanim["olcut"][:120])}…</em>
<span class="tur-ok">{ik("ok")}</span></a>"""

    kirintilar = [("/", "Ana sayfa"), ("/liste/", "Listeler")]
    icerik = f"""<section class="bl kap">
<div class="bl-bas"><div><h1>Sıralı listeler</h1>
<p>Belirli bir ölçüte göre süzülüp sıralanmış tesis listeleri. Her listenin
sıralama ölçütü sayfasında yazılı; elle seçim veya öne çıkarma yapılmaz.</p>
</div></div>
<div class="tur-iz">{kartlar}</div></section>"""
    return kabuk(
        baslik="Sıralı listeler — en yakın, en ucuz, havuzlu kamu tesisleri",
        aciklama="Ankara, İstanbul ve İzmir'e en yakın deniz tesisleri; havuzlu, "
        "çocuklu ailelere uygun ve fiyatı en düşük kamu misafirhaneleri.",
        yol="/liste/",
        icerik=icerik,
        kirintilar=kirintilar,
        aktif="/liste/",
        jsonld=[kirinti_ld(kirintilar)],
    )
