"""İl görsellerini Wikimedia Commons'tan toplar.

Tesislerin kendi fotoğrafı elimizde yok; olmayan fotoğrafı uydurmak yerine
her il için o ilin gerçek, serbest lisanslı bir fotoğrafını kullanıyoruz.
Fotoğraf sayfada "ilin fotoğrafı" olarak etiketleniyor, tesisin değil.

Lisans gereği yazar + lisans adı + kaynak sayfa saklanır ve sayfada gösterilir.
"""

from __future__ import annotations

import io
import json
import re
import sys
import time
import urllib.parse
import urllib.request
from pathlib import Path

from PIL import Image

KOK = Path(__file__).resolve().parent.parent
IMG = KOK / "img" / "il"
UA = {"User-Agent": "kamumisafirhaneler.com/1.0 (https://kamumisafirhaneler.com)"}

# 1200x675 (16:9) büyük, 640x360 kart. srcset ile ikisi de kullanılıyor.
BOYUTLAR = {"lg": (1200, 675), "sm": (640, 360)}
KALITE = 72

# Wikipedia sayfa adı ille birebir aynı değilse
SAYFA_ADI = {
    "İçel": "Mersin",
    "K. Maraş": "Kahramanmaraş",
    "K.Maraş": "Kahramanmaraş",
    "Hakkari": "Hakkâri (il)",
    "Ordu": "Ordu (il)",
    "Tokat": "Tokat (il)",
    "Bilecik": "Bilecik (il)",
}


def _get(url: str) -> dict:
    with urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=30) as r:
        return json.load(r)


def _temiz(html: str | None) -> str:
    if not html:
        return ""
    metin = re.sub(r"<[^>]+>", " ", html)
    metin = urllib.parse.unquote(metin)
    return re.sub(r"\s+", " ", metin).strip()


def il_gorseli(il: str) -> dict | None:
    """İlin Wikipedia sayfa görselini ve lisans bilgisini döndürür."""
    baslik = SAYFA_ADI.get(il, il)
    q = urllib.parse.urlencode(
        {
            "action": "query",
            "format": "json",
            "formatversion": "2",
            "titles": baslik,
            "prop": "pageimages",
            "piprop": "original|name",
            "pilicense": "free",
        }
    )
    sayfa = _get("https://tr.wikipedia.org/w/api.php?" + q)["query"]["pages"][0]
    dosya = sayfa.get("pageimage")
    kaynak = (sayfa.get("original") or {}).get("source")
    if not dosya or not kaynak:
        return None

    q2 = urllib.parse.urlencode(
        {
            "action": "query",
            "format": "json",
            "formatversion": "2",
            "titles": f"File:{dosya}",
            "prop": "imageinfo",
            "iiprop": "extmetadata|url",
            "iiurlwidth": "1600",
        }
    )
    bilgi = _get("https://commons.wikimedia.org/w/api.php?" + q2)["query"]["pages"][0]
    ii = (bilgi.get("imageinfo") or [{}])[0]
    meta = ii.get("extmetadata") or {}

    def m(anahtar: str) -> str:
        return _temiz((meta.get(anahtar) or {}).get("value"))

    return {
        "indir": ii.get("thumburl") or kaynak,
        "yazar": m("Artist") or "Bilinmiyor",
        "lisans": m("LicenseShortName") or "Wikimedia Commons",
        "lisans_url": m("LicenseUrl"),
        "sayfa": ii.get("descriptionurl") or f"https://commons.wikimedia.org/wiki/File:{dosya}",
        "aciklama": m("ImageDescription")[:200],
    }


def kirp_kaydet(veri: bytes, hedef_kok: Path, ad: str) -> dict:
    """16:9 merkez kırpma, iki boyutta webp."""
    im = Image.open(io.BytesIO(veri))
    if im.mode not in ("RGB", "L"):
        im = im.convert("RGB")

    g, y = im.size
    istenen = 16 / 9
    if g / y > istenen:  # çok geniş -> yanlardan kırp
        yeni_g = int(y * istenen)
        sol = (g - yeni_g) // 2
        im = im.crop((sol, 0, sol + yeni_g, y))
    else:  # çok uzun -> üst üçte birlik alanı koru (gökyüzü/siluet)
        yeni_y = int(g / istenen)
        ust = int((y - yeni_y) * 0.35)
        im = im.crop((0, ust, g, ust + yeni_y))

    cikti = {}
    for etiket, (bg, by) in BOYUTLAR.items():
        kopya = im.resize((bg, by), Image.LANCZOS)
        yol = hedef_kok / f"{ad}-{etiket}.webp"
        kopya.save(yol, "WEBP", quality=KALITE, method=6)
        cikti[etiket] = yol.name
    return cikti


def main() -> int:
    from veri import slug

    tesisler = json.loads((KOK / "tesisler.json").read_text("utf-8"))["tesisler"]
    iller = sorted({t["il"] for t in tesisler})
    IMG.mkdir(parents=True, exist_ok=True)

    hedef = KOK / "data" / "gorseller.json"
    sonuc = json.loads(hedef.read_text("utf-8")) if hedef.exists() else {}

    for i, il in enumerate(iller, 1):
        if il in sonuc:
            continue
        try:
            g = il_gorseli(il)
            if not g:
                print(f"{i:3}/{len(iller)} {il:20} görsel yok")
                continue
            with urllib.request.urlopen(
                urllib.request.Request(g["indir"], headers=UA), timeout=60
            ) as r:
                ham = r.read()
            dosyalar = kirp_kaydet(ham, IMG, slug(il))
            g.pop("indir")
            sonuc[il] = {**g, **dosyalar}
            print(f"{i:3}/{len(iller)} {il:20} {len(ham)//1024:5} KB -> {dosyalar['lg']}")
        except Exception as e:  # ağ hatası tek ili düşürsün, tümünü değil
            print(f"{i:3}/{len(iller)} {il:20} HATA {type(e).__name__}: {e}")
        hedef.write_text(json.dumps(sonuc, ensure_ascii=False, indent=1), "utf-8")
        time.sleep(0.4)

    print(f"\n{len(sonuc)}/{len(iller)} il görseli hazır")
    return 0


if __name__ == "__main__":
    sys.path.insert(0, str(Path(__file__).parent))
    raise SystemExit(main())
