"""Kurum amblemlerini resmi sitelerin ikon dosyalarindan alir (hepsi kare, dogrulanabilir)."""
from __future__ import annotations
import io, json, re, sys, urllib.parse, urllib.request
from pathlib import Path
from PIL import Image

KOK = Path(__file__).resolve().parent.parent
HEDEF = KOK / "img" / "kurum"
UA = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0 Safari/537.36"}
sys.path.insert(0, str(Path(__file__).parent))
from logo import KURUMLAR  # noqa: E402
from veri import slug  # noqa: E402

def ac(url, ikili=False):
    r = urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=25)
    b = r.read()
    return b if ikili else b.decode("utf-8", "replace")

def ikon_adaylari(site):
    adaylar = []
    try:
        html = ac(site)
    except Exception:
        html = ""
    for m in re.finditer(r'<link[^>]+>', html, re.I):
        t = m.group(0)
        if not re.search(r'rel\s*=\s*["\'][^"\']*icon', t, re.I):
            continue
        h = re.search(r'href\s*=\s*["\']([^"\']+)', t, re.I)
        if not h:
            continue
        boy = re.search(r'sizes\s*=\s*["\'](\d+)', t, re.I)
        puan = int(boy.group(1)) if boy else (180 if "apple" in t.lower() else 32)
        adaylar.append((puan, urllib.parse.urljoin(site, h.group(1))))
    for yol in ("apple-touch-icon.png", "apple-touch-icon-precomposed.png", "favicon.ico"):
        adaylar.append((60, urllib.parse.urljoin(site, "/" + yol)))
    adaylar.sort(key=lambda x: -x[0])
    gor, out = set(), []
    for _, u in adaylar:
        if u not in gor:
            gor.add(u); out.append(u)
    return out[:6]

def main():
    HEDEF.mkdir(parents=True, exist_ok=True)
    yol = KOK / "data" / "kurumlar.json"
    cikti = {}
    for kisa, (tam, site, _) in KURUMLAR.items():
        ad = slug(kisa); dosya = None
        for u in ikon_adaylari(site):
            try:
                ham = ac(u, True)
                im = Image.open(io.BytesIO(ham))
                if getattr(im, "n_frames", 1) > 1 or im.format == "ICO":
                    im = Image.open(io.BytesIO(ham)); im.size  # en buyuk kare
                if im.width < 48:
                    continue
                im = im.convert("RGBA")
                k = max(im.size)
                tuval = Image.new("RGBA", (k, k), (0, 0, 0, 0))
                tuval.alpha_composite(im, ((k - im.width) // 2, (k - im.height) // 2))
                tuval = tuval.resize((256, 256), Image.LANCZOS)
                p = HEDEF / f"{ad}.png"; tuval.save(p, "PNG", optimize=True)
                dosya = p.name; break
            except Exception:
                continue
        cikti[kisa] = {"ad": tam, "site": site, "dosya": dosya}
        print(f"{kisa:32} {dosya or 'YOK'}")
    yol.write_text(json.dumps(cikti, ensure_ascii=False, indent=1), "utf-8")
    print(f"\n{sum(1 for v in cikti.values() if v['dosya'])}/{len(KURUMLAR)} amblem")

main()
