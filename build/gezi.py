"""Tesislerin çevresindeki gezilecek yerleri Vikipedi'den toplar.

Yaklaşım: elimizdeki 561 koordinatın her biri için Vikipedi'nin konum araması
(`list=geosearch`) çalıştırılır. Dönen her kayıt gerçek, adı konmuş ve konumu
bilinen bir yerdir; mesafe de koordinattan hesaplanır. Böylece "şu tesise 600 m
mesafede Sinop Kalesi var" gibi, uydurulmamış ve başka hiçbir dizinde olmayan
bir bilgi çıkar.

Metinler Vikipedi'den alınır (CC BY-SA 4.0) ve sayfada kaynak gösterilir.
Hiçbir açıklama uydurulmaz; Vikipedi'de karşılığı olmayan yer listeye girmez.
"""

from __future__ import annotations

import json
import re
import sys
import time
import urllib.parse
import urllib.request
from collections import defaultdict
from pathlib import Path

KOK = Path(__file__).resolve().parent.parent
HEDEF = KOK / "data" / "gezi.json"
UA = {"User-Agent": "kamumisafirhaneler.com/1.0 (https://kamumisafirhaneler.com)"}
API = "https://tr.wikipedia.org/w/api.php?"
YARICAP = 10000  # Vikipedi'nin izin verdiği azami değer

# Gezilecek yer sayılmayanlar — adında bunlar geçen kayıt listeye girmez
_ELE = re.compile(
    r"havaliman|havaalan|stadyum|stadı|hastane|üniversite|fakülte|"
    r"belediye|valilik|kaymakam|otogar|garı|istasyon|okulu|lisesi|"
    r"organize sanayi|toplu konut|mahallesi|köyü|barajı|santral|"
    r"cezaevi̇ müdürlüğü|adliye|karakol|(il|ilçe)si$|spor kulübü|"
    r"anadolu otoyolu|otoyolu|tüneli|viyadük",
    re.IGNORECASE,
)

# Tür tanıma: Vikidata açıklaması ya da başlık bu kalıplara bakılarak etiketlenir
TURLER = [
    ("kale", r"kale|hisar|sur\b|kulesi"),
    ("muze", r"müze|ören yeri|arkeoloji"),
    ("cami", r"cami|mescit|külliye|medrese|türbe|kümbet"),
    ("kilise", r"kilise|manastır|katedral|sinagog"),
    ("antik", r"antik|harabe|ören|höyük|nekropol|amfitiyatro|tiyatro\b|agora"),
    ("deniz", r"plaj|koy\b|kumsal|sahil|liman|ada\b|yarımada|burun|fener"),
    ("doga", r"şelale|mağara|göl\b|kanyon|yayla|milli park|tabiat|dağı|ormanı|vadi"),
    ("kopru", r"köprü|kemer|su kemeri"),
    ("meydan", r"meydan|park|bahçe|çarşı|han\b|hamam|konak|ev müzesi|saat kulesi"),
]

TUR_ADI = {
    "kale": "Kale ve surlar",
    "muze": "Müze ve ören yeri",
    "cami": "Cami, medrese ve türbe",
    "kilise": "Kilise ve manastır",
    "antik": "Antik yerleşim",
    "deniz": "Deniz ve sahil",
    "doga": "Doğa",
    "kopru": "Tarihî köprü",
    "meydan": "Meydan, çarşı ve tarihî yapı",
    "diger": "Görülecek diğer yerler",
}


def _api(params: dict) -> dict:
    p = {"format": "json", "formatversion": "2", **params}
    url = API + urllib.parse.urlencode(p)
    with urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=30) as r:
        return json.load(r)


def yakindakiler(lat: float, lon: float, adet: int = 50) -> list[dict]:
    d = _api({
        "action": "query", "list": "geosearch",
        "gscoord": f"{lat}|{lon}", "gsradius": YARICAP, "gslimit": adet,
    })
    return d.get("query", {}).get("geosearch", [])


def ayrinti(basliklar: list[str]) -> dict[str, dict]:
    """Başlık -> {ozet, aciklama, gorsel}. En fazla 20 başlık tek istekte."""
    if not basliklar:
        return {}
    d = _api({
        "action": "query", "titles": "|".join(basliklar[:20]),
        "prop": "extracts|pageterms|pageimages",
        "exintro": "1", "explaintext": "1", "exsentences": "3",
        "piprop": "thumbnail", "pithumbsize": "480",
    })
    cikti = {}
    for s in d.get("query", {}).get("pages", []):
        if s.get("missing"):
            continue
        terim = s.get("terms") or {}
        cikti[s["title"]] = {
            "ozet": re.sub(r"\s+", " ", (s.get("extract") or "")).strip(),
            "aciklama": (terim.get("description") or [""])[0],
            "gorsel": (s.get("thumbnail") or {}).get("source", ""),
        }
    return cikti


def turu(baslik: str, aciklama: str) -> str:
    metin = f"{baslik} {aciklama}".lower()
    for anahtar, kalip in TURLER:
        if re.search(kalip, metin):
            return anahtar
    return "diger"


def uygun_mu(baslik: str, ayr: dict) -> bool:
    if _ELE.search(baslik):
        return False
    ozet = ayr.get("ozet", "")
    # Vikipedi'de karşılığı olmayan ya da tek cümlelik taslak sayfalar alınmaz
    return len(ozet) >= 60


def main() -> int:
    sys.path.insert(0, str(Path(__file__).parent))
    from veri import tesis_slug

    tesisler = json.loads((KOK / "tesisler.json").read_text("utf-8"))["tesisler"]
    konumlar = {
        k: v for k, v in json.loads(
            (KOK / "data" / "konumlar.json").read_text("utf-8")
        ).items() if v
    }

    # Arama her tesisin kendi konumundan yapılır. Aynı ilçede iki tesis varsa
    # ikisinin çevresi de taranır ve sonuçlar birleştirilir; yoksa yalnızca
    # rastgele seçilen tesisin çevresi görünür ve diğerine 600 m mesafedeki
    # kale listede hiç çıkmaz.
    noktalar: dict[str, list[tuple[float, float]]] = defaultdict(list)
    for t in tesisler:
        k = konumlar.get(tesis_slug(t))
        if not k:
            continue
        anahtar = f"{t['il']}|{t['ilce']}"
        nokta = (round(k["lat"], 4), round(k["lon"], 4))
        if nokta not in noktalar[anahtar]:
            noktalar[anahtar].append(nokta)

    sonuc = json.loads(HEDEF.read_text("utf-8")) if HEDEF.exists() else {}
    toplam = len(noktalar)
    for i, (anahtar, koordinatlar) in enumerate(sorted(noktalar.items()), 1):
        if anahtar in sonuc:
            continue
        birlesik: dict[str, dict] = {}
        try:
            for lat, lon in koordinatlar[:3]:
                ham = yakindakiler(lat, lon)
                time.sleep(0.25)
                basliklar = [x["title"] for x in ham if not _ELE.search(x["title"])]
                ayr = {}
                for j in range(0, min(len(basliklar), 40), 20):
                    ayr.update(ayrinti(basliklar[j:j + 20]))
                    time.sleep(0.25)
                for x in ham:
                    a = ayr.get(x["title"])
                    if not a or not uygun_mu(x["title"], a):
                        continue
                    km = round(x["dist"] / 1000, 1)
                    onceki = birlesik.get(x["title"])
                    if onceki and onceki["km"] <= km:
                        continue
                    birlesik[x["title"]] = {
                        "ad": x["title"], "km": km,
                        "lat": x["lat"], "lon": x["lon"],
                        "tur": turu(x["title"], a["aciklama"]),
                        "aciklama": a["aciklama"][:120],
                        "ozet": a["ozet"][:420],
                        "gorsel": a["gorsel"],
                    }
            yerler = sorted(birlesik.values(), key=lambda y: y["km"])
            sonuc[anahtar] = yerler
            print(f"{i:3}/{toplam} {anahtar:34} {len(yerler):2} yer "
                  f"({len(koordinatlar)} tesis noktası)")
        except Exception as ex:
            print(f"{i:3}/{toplam} {anahtar:34} HATA {type(ex).__name__}: {ex}")
            sonuc.setdefault(anahtar, [])
        if i % 10 == 0 or i == toplam:
            HEDEF.write_text(json.dumps(sonuc, ensure_ascii=False), "utf-8")

    HEDEF.write_text(json.dumps(sonuc, ensure_ascii=False), "utf-8")
    dolu = sum(1 for v in sonuc.values() if v)
    yer = sum(len(v) for v in sonuc.values())
    print(f"\n{dolu}/{len(sonuc)} ilçede toplam {yer} gezilecek yer")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
