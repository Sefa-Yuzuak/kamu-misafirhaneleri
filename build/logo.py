"""Veri kaynağı kurumların logolarını kendi resmî sitelerinden indirir.

Logolar kurumlara aittir; burada yalnızca verinin hangi kurumdan geldiğini
göstermek ve o kuruma bağlantı vermek için kullanılıyor.
Sayfada gri gösterilip fare üzerine gelince renklenir.
"""

from __future__ import annotations

import io
import json
import re
import sys
import urllib.parse
import urllib.request
from pathlib import Path

from PIL import Image

KOK = Path(__file__).resolve().parent.parent
HEDEF = KOK / "img" / "kurum"
UA = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/126.0 Safari/537.36"
    )
}

# kısa ad -> (tam ad, site, aday logo yolları)
KURUMLAR = {
    "MEB": ("Millî Eğitim Bakanlığı", "https://www.meb.gov.tr/", []),
    "EGM": ("Emniyet Genel Müdürlüğü", "https://www.egm.gov.tr/", []),
    "Tarım ve Orman Bakanlığı": (
        "Tarım ve Orman Bakanlığı", "https://www.tarimorman.gov.tr/", []),
    "Adalet Bakanlığı": ("Adalet Bakanlığı", "https://www.adalet.gov.tr/", []),
    "Sağlık Bakanlığı": ("Sağlık Bakanlığı", "https://www.saglik.gov.tr/", []),
    "Orman Genel Müdürlüğü": (
        "Orman Genel Müdürlüğü", "https://www.ogm.gov.tr/", []),
    "DSİ": ("Devlet Su İşleri", "https://www.dsi.gov.tr/", []),
    "TKİ": ("Türkiye Kömür İşletmeleri", "https://www.tki.gov.tr/", []),
    "İLKSAN": ("İlkokul Öğretmenleri Sağlık ve Sosyal Yardım Sandığı",
               "https://www.ilksan.gov.tr/", []),
    "Ankara Üniversitesi": ("Ankara Üniversitesi", "https://www.ankara.edu.tr/", []),
    "Ege Üniversitesi": ("Ege Üniversitesi", "https://ege.edu.tr/", []),
    "Boğaziçi Üniversitesi": ("Boğaziçi Üniversitesi", "https://bogazici.edu.tr/", []),
    "İstanbul Teknik Üniversitesi": ("İstanbul Teknik Üniversitesi", "https://www.itu.edu.tr/", []),
    "Akdeniz Üniversitesi": ("Akdeniz Üniversitesi", "https://www.akdeniz.edu.tr/", []),
    "Dokuz Eylül Üniversitesi": ("Dokuz Eylül Üniversitesi", "https://www.deu.edu.tr/", []),
    "Ondokuz Mayıs Üniversitesi": ("Ondokuz Mayıs Üniversitesi", "https://www.omu.edu.tr/", []),
}

_LOGO_IPUCU = re.compile(r"logo|amblem|brand|header", re.I)


def _ac(url: str, ikili: bool = False):
    r = urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=25)
    ham = r.read()
    return ham if ikili else ham.decode("utf-8", "replace")


def logo_adaylari(site: str) -> list[str]:
    """Ana sayfadan olası logo adreslerini çıkarır, iyiden kötüye sıralı."""
    try:
        html = _ac(site)
    except Exception:
        return []
    adaylar: list[tuple[int, str]] = []

    for m in re.finditer(r'<(?:img|source)[^>]+>', html, re.I):
        etiket = m.group(0)
        src = re.search(r'(?:src|data-src|srcset)\s*=\s*["\']([^"\']+)', etiket, re.I)
        if not src:
            continue
        yol = src.group(1).split()[0]
        puan = 0
        if _LOGO_IPUCU.search(etiket):
            puan += 10
        if yol.lower().endswith(".svg"):
            puan += 4
        if yol.lower().endswith((".png", ".webp")):
            puan += 2
        if puan:
            adaylar.append((puan, yol))

    for etiket in ('meta[property="og:image"]', "apple-touch-icon"):
        pass
    og = re.search(r'<meta[^>]+og:image["\'][^>]*content=["\']([^"\']+)', html, re.I)
    if og:
        adaylar.append((1, og.group(1)))
    ati = re.search(r'<link[^>]+apple-touch-icon[^>]*href=["\']([^"\']+)', html, re.I)
    if ati:
        adaylar.append((3, ati.group(1)))

    adaylar.sort(key=lambda x: -x[0])
    goruldu, sonuc = set(), []
    for _, yol in adaylar:
        tam = urllib.parse.urljoin(site, yol)
        if tam not in goruldu:
            goruldu.add(tam)
            sonuc.append(tam)
    return sonuc[:8]


def indir_kaydet(adaylar: list[str], ad: str) -> str | None:
    """İlk kullanılabilir logoyu 240px yüksekliğinde şeffaf PNG olarak kaydeder."""
    for url in adaylar:
        try:
            ham = _ac(url, ikili=True)
        except Exception:
            continue
        if url.lower().endswith(".svg") or ham[:200].lstrip().startswith(b"<svg"):
            yol = HEDEF / f"{ad}.svg"
            yol.write_bytes(ham)
            return yol.name
        try:
            im = Image.open(io.BytesIO(ham))
        except Exception:
            continue
        if im.width < 40 or im.height < 40:
            continue
        im = im.convert("RGBA")
        oran = 240 / im.height
        im = im.resize((max(1, int(im.width * oran)), 240), Image.LANCZOS)
        if im.width > 900:
            continue  # afiş/banner, logo değil
        yol = HEDEF / f"{ad}.png"
        im.save(yol, "PNG", optimize=True)
        return yol.name
    return None


def main() -> int:
    from veri import slug

    HEDEF.mkdir(parents=True, exist_ok=True)
    cikti_yolu = KOK / "data" / "kurumlar.json"
    cikti = json.loads(cikti_yolu.read_text("utf-8")) if cikti_yolu.exists() else {}

    for kisa, (tam, site, _) in KURUMLAR.items():
        if kisa in cikti and cikti[kisa].get("dosya"):
            continue
        ad = slug(kisa)
        dosya = indir_kaydet(logo_adaylari(site), ad)
        cikti[kisa] = {"ad": tam, "site": site, "dosya": dosya}
        print(f"{kisa:32} {dosya or 'LOGO YOK'}")
        cikti_yolu.write_text(json.dumps(cikti, ensure_ascii=False, indent=1), "utf-8")

    var = sum(1 for v in cikti.values() if v.get("dosya"))
    print(f"\n{var}/{len(KURUMLAR)} kurum logosu indirildi")
    return 0


if __name__ == "__main__":
    sys.path.insert(0, str(Path(__file__).parent))
    raise SystemExit(main())
