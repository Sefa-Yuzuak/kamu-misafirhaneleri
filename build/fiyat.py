"""Yayimlanan fiyat metnini statü × oda tipi tablosuna ayristirir.

KURAL: yalnizca kesin ayristirilan metin tabloya donusur; gerisi oldugu gibi
serbest metin olarak basilir. Ayristirici hicbir tutari tahmin etmez, eksik
hucreyi doldurmaz. Bir parcada birden fazla tutar, ayni hucre icin farkli iki
tutar ya da tanimadigi bir kalip varsa TABLO URETMEZ (None doner).

Rakip olcumu (13.09.2026): polisevi.net ve ogretmenevine.com fiyati
"statü × oda tipi" tablosu + Offer semasiyla basiyor; bizde 63 tesisin fiyati
tek satir serbest metindi. Tablo hem okunur hem makine-okunur.

Metin dilbilgisi (kurum sayfalarindan derlenen 63 kayit uzerinde olculdu):
    metin   := parca (" · " parca)*
    parca   := ETIKET ":" oge ("," oge)*        # "Tek Kişilik: Öğretmen 675 TL, Kamu 1.000 TL"
             | ETIKET ":" TUTAR                 # "Kamu: 900 TL"
    oge     := AD TUTAR                         # "Kamu 1.000 TL"
Satir etiketi bazen statü (Sivil: ...), bazen oda tipi (Tek Kişilik: ...);
tablo icin fark etmez, ilk sutun etiket, kalan sutunlar oge adlaridir.
"""
from __future__ import annotations

import re

from veri import tr_baslik

_TUTAR_SON = re.compile(
    r"^(?P<ad>.*?)\s*(?P<tutar>\d{1,3}(?:\.\d{3})+|\d{3,6})(?:[,.]\d{2})?\s*(?:TL|₺)"
    r"\s*(?:/\s*ki[şs]i)?\s*\.?$",
    re.I,
)
_TUTAR_SAY = re.compile(r"\d{1,3}(?:\.\d{3})+|\d{3,6}")
_AYRAC = " · "


def _tutar(ham: str) -> int:
    return int(ham.replace(".", ""))


def _oge(metin: str) -> tuple[str, int] | None:
    """'Kamu 1.000 TL' -> ('Kamu', 1000). Birden fazla tutar varsa None."""
    m = _TUTAR_SON.match(metin.strip())
    if not m:
        return None
    if len(_TUTAR_SAY.findall(metin)) != 1 and not re.search(r"\(%\d+\)", metin):
        # "1600,00 TL (indirimli) 1.800 TL" gibi cift tutarli parca tabloya giremez.
        # "Öğretmen(%50) 350 TL" ise tek tutar + indirim orani: kabul.
        return None
    ad = m.group("ad").strip(" -:")
    if re.search(r"TL|₺|:", ad, re.I):
        # "70 0 TL · Odanın ... : 900 TL": ayraç bozuk, iki parça tek ögeye
        # sıkışmış; tablo yerine metin basılır.
        return None
    if ad.count("(") == ad.count(")") + 1:
        ad += ")"  # "Üye(tüm MEB Personeli" — kaynakta kapanmamış parantez
    return _temiz_ad(ad), _tutar(m.group("tutar"))


def _temiz_ad(ad: str) -> str:
    ad = re.sub(r"\s+", " ", ad).strip()
    if ad and ad == ad.upper() and any(c.isalpha() for c in ad):
        ad = tr_baslik(ad)
    return ad


def tablo(metin: str | None) -> list[tuple[str, list[tuple[str, int]]]] | None:
    """[(satir_etiketi, [(sutun_adi, tutar), ...]), ...] ya da None.

    Sutun adi bos olabilir ("Kamu: 900 TL" -> ("Kamu", [("", 900)])).
    """
    if not metin or _AYRAC not in metin and ":" not in metin:
        return None
    satirlar: dict[str, dict[str, int]] = {}
    sira: list[str] = []
    for parca in metin.split(_AYRAC):
        parca = parca.strip()
        if ":" not in parca:
            return None
        etiket, _, kalan = parca.partition(":")
        etiket = _temiz_ad(etiket)
        if not etiket or not kalan.strip():
            return None
        ogeler = []
        for ham in kalan.split(","):
            o = _oge(ham)
            if o is None:
                return None
            ogeler.append(o)
        if len(ogeler) > 1 and any(not ad for ad, _ in ogeler):
            return None  # "Kamu: 900 TL, 1200 TL" — hangi tutar ne, belirsiz
        satir = satirlar.setdefault(etiket, {})
        if etiket not in sira:
            sira.append(etiket)
        for ad, tutar in ogeler:
            if ad in satir and satir[ad] != tutar:
                return None  # ayni hucre icin iki farkli tutar
            satir[ad] = tutar
    if not satirlar:
        return None
    return [(et, list(satirlar[et].items())) for et in sira]


def sutunlar(t: list[tuple[str, list[tuple[str, int]]]]) -> list[str]:
    """Satirlarda gecen oge adlarinin ilk gorulme sirasiyla birlesimi."""
    s: list[str] = []
    for _, ogeler in t:
        for ad, _ in ogeler:
            if ad not in s:
                s.append(ad)
    return s


def para(tutar: int) -> str:
    return f"{tutar:,}".replace(",", ".") + " TL"


def html(t: list[tuple[str, list[tuple[str, int]]]], e) -> str:
    """Tablo HTML'i. Dar ekranda satir karta donusur (td[data-etiket])."""
    sut = sutunlar(t)
    tek = sut == [""]
    bas = "".join(f"<th>{e(s) if s else 'Fiyat'}</th>" for s in sut)
    govde = []
    for etiket, ogeler in t:
        h = dict(ogeler)
        hucreler = "".join(
            f'<td data-etiket="{e(s) if s else "Fiyat"}">{para(h[s]) if s in h else "—"}</td>'
            for s in sut
        )
        govde.append(f"<tr><th scope=\"row\">{e(etiket)}</th>{hucreler}</tr>")
    sinif = "fyt fyt-tek" if tek else "fyt"
    return (
        f'<div class="tablo-sar"><table class="{sinif}">'
        f"<thead><tr><th></th>{bas}</tr></thead>"
        f"<tbody>{''.join(govde)}</tbody></table></div>"
    )


def teklifler(t: list[tuple[str, list[tuple[str, int]]]], kaynak: str | None) -> list[dict]:
    """schema.org Offer listesi: yalnizca tesisin yayimladigi tutarlar."""
    cikti = []
    for etiket, ogeler in t:
        for ad, tutar in ogeler:
            o = {
                "@type": "Offer",
                "name": f"{etiket} — {ad}" if ad else etiket,
                "price": tutar,
                "priceCurrency": "TRY",
                "availability": "https://schema.org/InStock",
            }
            if kaynak:
                o["url"] = kaynak
            cikti.append(o)
    return cikti
