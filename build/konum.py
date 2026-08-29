"""Tesis koordinatlarını OpenStreetMap Nominatim üzerinden toplar.

İki kademe:
  1. Tesisin kendi adıyla arama — OSM'de kayıtlıysa gerçek konum bulunur.
  2. Bulunamazsa ilçe merkezi — yaklaşık konum, işaretlenerek saklanır.

`kesinlik` alanı hangi kademenin kullanıldığını söyler; sayfada bu ayrım
kullanıcıya da gösterilir ve schema.org geo yalnızca "tesis" için yazılır.

Nominatim kullanım şartı gereği saniyede bir istek yapılır ve kimlik bildirilir.
"""

from __future__ import annotations

import json
import sys
import time
import urllib.parse
import urllib.request
from pathlib import Path

KOK = Path(__file__).resolve().parent.parent
HEDEF = KOK / "data" / "konumlar.json"
UA = {"User-Agent": "kamumisafirhaneler.com/1.0 (https://kamumisafirhaneler.com)"}
API = "https://nominatim.openstreetmap.org/search?"

# Türkiye sınırları — dışına düşen sonuç kabul edilmez
SINIR = (35.5, 42.5, 25.5, 45.0)  # min_lat, max_lat, min_lon, max_lon

_ANAHTAR = ("ogretmenevi", "polisevi", "misafirhane", "hotel", "guest_house", "tourism")


def sorgu(metin: str, tur: str = "") -> list[dict]:
    p = {
        "q": metin,
        "format": "jsonv2",
        "countrycodes": "tr",
        "limit": "5",
        "addressdetails": "1",
    }
    url = API + urllib.parse.urlencode(p)
    with urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=30) as r:
        return json.load(r)


def _icerde(lat: float, lon: float) -> bool:
    a, b, c, d = SINIR
    return a <= lat <= b and c <= lon <= d


def _ilce_uyar(sonuc: dict, ilce: str, il: str) -> bool:
    adres = sonuc.get("address") or {}
    hepsi = " ".join(str(v).lower() for v in adres.values())
    return ilce.lower() in hepsi or il.lower() in hepsi


def tesis_konumu(t: dict, ilce_hazir: dict | None = None) -> dict | None:
    """Önce tesis adı (iki biçimde), sonra ilçe merkezi."""
    ad = t["ad"].replace("ve Akşam Sanat Okulu", "").strip()
    denemeler = [
        (ad, "tesis"),
        (f"{ad}, {t['ilce']}, {t['il']}", "tesis"),
    ]
    if not ilce_hazir:
        denemeler.append((f"{t['ilce']}, {t['il']}, Türkiye", "ilce"))
    for metin, kesinlik in denemeler:
        try:
            sonuclar = sorgu(metin)
        except Exception:
            time.sleep(2)
            continue
        finally:
            time.sleep(1.1)
        for s in sonuclar:
            try:
                lat, lon = float(s["lat"]), float(s["lon"])
            except (KeyError, ValueError):
                continue
            if not _icerde(lat, lon):
                continue
            if kesinlik == "tesis" and not _ilce_uyar(s, t["ilce"], t["il"]):
                continue
            return {
                "lat": round(lat, 6),
                "lon": round(lon, 6),
                "kesinlik": kesinlik,
                "osm": s.get("display_name", "")[:120],
            }
    return dict(ilce_hazir) if ilce_hazir else None


def main() -> int:
    tesisler = json.loads((KOK / "tesisler.json").read_text("utf-8"))["tesisler"]
    sonuc = json.loads(HEDEF.read_text("utf-8")) if HEDEF.exists() else {}
    ilce_onbellek: dict[str, dict] = {
        f"{v['il']}|{v['ilce']}": v
        for v in sonuc.values()
        if v and v.get("kesinlik") == "ilce" and v.get("il")
    }

    sys.path.insert(0, str(Path(__file__).parent))
    from veri import tesis_slug

    for i, t in enumerate(tesisler, 1):
        s = tesis_slug(t)
        if s in sonuc:
            continue
        anahtar = f"{t['il']}|{t['ilce']}"
        k = tesis_konumu(t, ilce_onbellek.get(anahtar))
        if k and k["kesinlik"] == "ilce":
            ilce_onbellek[anahtar] = {**k, "il": t["il"], "ilce": t["ilce"]}
        sonuc[s] = ({**k, "il": t["il"], "ilce": t["ilce"]} if k else None)
        etiket = k["kesinlik"] if k else "YOK"
        print(f"{i:3}/{len(tesisler)} {etiket:5} {t['ad'][:46]}")
        if i % 10 == 0 or i == len(tesisler):
            HEDEF.write_text(json.dumps(sonuc, ensure_ascii=False, indent=1), "utf-8")

    HEDEF.write_text(json.dumps(sonuc, ensure_ascii=False, indent=1), "utf-8")
    kesin = sum(1 for v in sonuc.values() if v and v["kesinlik"] == "tesis")
    yakl = sum(1 for v in sonuc.values() if v and v["kesinlik"] == "ilce")
    print(f"\n{kesin} tesis konumu + {yakl} ilçe merkezi = {kesin + yakl}/{len(tesisler)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
