"""Üretilen sitenin baştan sona denetimi: python build/denetim.py

Kırık bağlantı, eksik görsel, bozuk şema, tekrarlanan başlık, erişilebilirlik
ve içerik tutarlılığı. Bulgu varsa çıkış kodu 1.
"""

from __future__ import annotations

import json
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path
from urllib.parse import unquote, urlparse

KOK = Path(__file__).resolve().parent.parent
SITE = KOK / "site"
ALAN = "https://kamumisafirhaneler.com"

bulgular: list[tuple[str, str, str]] = []  # (agirlik, sayfa, mesaj)


def bul(agirlik: str, sayfa: str, mesaj: str) -> None:
    bulgular.append((agirlik, sayfa, mesaj))


def yol_of(p: Path) -> str:
    r = p.relative_to(SITE).as_posix()
    return "/" + (r[: -len("index.html")] if r.endswith("index.html") else r)


def hedef_var(hedef: str) -> bool:
    h = unquote(hedef.split("#")[0].split("?")[0])
    if not h.startswith("/"):
        return True
    p = SITE / h.lstrip("/")
    if h.endswith("/"):
        return (p / "index.html").exists()
    return p.exists() or (p / "index.html").exists()


def main() -> int:
    sayfalar = sorted(SITE.rglob("*.html"))
    if not sayfalar:
        print("site/ boş — önce build/derle.py çalıştırın")
        return 1

    basliklar: Counter[str] = Counter()
    aciklamalar: Counter[str] = Counter()
    kanonikler: Counter[str] = Counter()
    ic_baglanti: dict[str, set[str]] = defaultdict(set)
    gorsel_sayisi = 0

    for p in sayfalar:
        y = yol_of(p)
        h = p.read_text("utf-8")

        # --- baş bilgisi
        m = re.search(r"<title>(.*?)</title>", h, re.S)
        if not m or not m.group(1).strip():
            bul("YUKSEK", y, "title yok veya boş")
        else:
            basliklar[m.group(1)] += 1
            if len(m.group(1)) > 70:
                bul("DUSUK", y, f"title {len(m.group(1))} karakter (>70)")

        m = re.search(r'<meta name="description" content="(.*?)">', h, re.S)
        if not m or not m.group(1).strip():
            bul("YUKSEK", y, "meta description yok")
        else:
            aciklamalar[m.group(1)] += 1
            n = len(m.group(1))
            if n > 165:
                bul("DUSUK", y, f"description {n} karakter (>165)")
            elif n < 60:
                bul("DUSUK", y, f"description {n} karakter (<60)")

        m = re.search(r'<link rel="canonical" href="(.*?)">', h)
        if not m:
            bul("YUKSEK", y, "canonical yok")
        else:
            kanonikler[m.group(1)] += 1
            if m.group(1) != ALAN + y:
                bul("YUKSEK", y, f"canonical uyumsuz: {m.group(1)}")

        if '<html lang="tr">' not in h:
            bul("ORTA", y, "lang=tr yok")

        # --- başlık hiyerarşisi
        h1 = re.findall(r"<h1[ >]", h)
        if len(h1) != 1:
            bul("ORTA", y, f"{len(h1)} adet h1 (1 olmalı)")

        # --- JSON-LD
        for blok in re.findall(
            r'<script type="application/ld\+json">(.*?)</script>', h, re.S
        ):
            try:
                d = json.loads(blok)
            except json.JSONDecodeError as ex:
                bul("YUKSEK", y, f"JSON-LD bozuk: {ex}")
                continue
            if "@type" not in d:
                bul("ORTA", y, "JSON-LD @type yok")
            if d.get("@type") == "FAQPage":
                for s in d.get("mainEntity", []):
                    c = s.get("acceptedAnswer", {}).get("text", "")
                    if not c.strip():
                        bul("ORTA", y, f"boş SSS cevabı: {s.get('name')}")

        # --- görseller
        for etiket in re.findall(r"<img\b[^>]*>", h):
            gorsel_sayisi += 1
            src = re.search(r'src="([^"]+)"', etiket)
            alt = re.search(r'alt="([^"]*)"', etiket)
            if not src:
                bul("YUKSEK", y, "img src yok")
                continue
            if alt is None:
                bul("ORTA", y, f"alt yok: {src.group(1)}")
            elif not alt.group(1).strip():
                bul("DUSUK", y, f"alt boş: {src.group(1)}")
            if not hedef_var(src.group(1)):
                bul("YUKSEK", y, f"görsel yok: {src.group(1)}")
            if 'width="' not in etiket or 'height="' not in etiket:
                bul("DUSUK", y, f"boyut yok (CLS): {src.group(1)}")

        # --- bağlantılar
        for hedef in re.findall(r'<a\b[^>]*href="([^"]+)"', h):
            if hedef.startswith(("mailto:", "tel:", "#")):
                continue
            u = urlparse(hedef)
            if u.scheme in ("http", "https"):
                if u.netloc.endswith("kamumisafirhaneler.com"):
                    bul("DUSUK", y, f"iç bağlantı mutlak yazılmış: {hedef}")
                continue
            ic_baglanti[hedef.split("#")[0]].add(y)
            if not hedef_var(hedef):
                bul("YUKSEK", y, f"kırık bağlantı: {hedef}")

        # --- varlıklar
        for hedef in re.findall(r'<link\b[^>]*href="(/[^"]+)"', h) + re.findall(
            r'<script\b[^>]*src="(/[^"]+)"', h
        ):
            if not hedef_var(hedef):
                bul("YUKSEK", y, f"varlık yok: {hedef}")

        # --- metin sağlığı
        if "�" in h:
            bul("YUKSEK", y, "bozuk karakter (U+FFFD) var")
        temiz = h.replace("{search_term_string}", "")  # SearchAction şablonu
        kalinti = re.search(r"\bNone\b|\bnan\b|\{[a-z_]+\}", temiz)
        if kalinti:
            kusur = kalinti.group(0)
            bul("ORTA", y, f"işlenmemiş şablon/None izi: {kusur}")

    # --- toplu kontroller
    for b, n in basliklar.items():
        if n > 1:
            bul("ORTA", "(genel)", f"{n} sayfada aynı title: {b[:60]}")
    for a, n in aciklamalar.items():
        if n > 1:
            bul("DUSUK", "(genel)", f"{n} sayfada aynı description: {a[:60]}")
    for c, n in kanonikler.items():
        if n > 1:
            bul("YUKSEK", "(genel)", f"{n} sayfada aynı canonical: {c}")

    # --- site haritası ile karşılaştır
    sm = (SITE / "sitemap.xml").read_text("utf-8")
    sm_yollar = {u.replace(ALAN, "") for u in re.findall(r"<loc>(.*?)</loc>", sm)}
    gercek = {yol_of(p) for p in sayfalar if p.name == "index.html"}
    for y in sorted(gercek - sm_yollar):
        bul("ORTA", y, "site haritasında yok")
    for y in sorted(sm_yollar - gercek):
        bul("YUKSEK", y, "site haritasında var ama sayfa yok")

    # --- öksüz sayfa (hiçbir yerden bağlanmayan)
    baglanilan = set(ic_baglanti)
    for y in sorted(gercek):
        if y != "/" and y not in baglanilan:
            bul("ORTA", y, "hiçbir sayfadan bağlantı verilmemiş (öksüz)")

    # --- JavaScript sözdizimi (node varsa)
    import shutil as _sh
    import subprocess

    if _sh.which("node"):
        for js in sorted((SITE / "static").glob("*.js")):
            r = subprocess.run(["node", "--check", str(js)], capture_output=True, text=True)
            if r.returncode != 0:
                ilk = (r.stderr or "").strip().splitlines()
                bul("YUKSEK", "/" + js.name,
                    "JavaScript sözdizimi hatası: " + " ".join(ilk[:3])[:150])

    # --- veri dosyaları
    for ad in ("data/ara.json", "tesisler.json", "robots.txt", "llms.txt", "404.html"):
        if not (SITE / ad).exists():
            bul("YUKSEK", "(genel)", f"eksik dosya: {ad}")

    hyol = SITE / "data" / "harita.json"
    if hyol.exists():
        hd = json.loads(hyol.read_text("utf-8"))
        for nokta in hd["t"]:
            if not hedef_var(f"/tesis/{nokta[3]}/"):
                bul("YUKSEK", "/harita/", f"harita noktası kırık: {nokta[3]}")
        kesin = sum(1 for x in hd["t"] if x[8])
        print(f"harita: {len(hd['t'])} nokta, {kesin} kesin konum")

    # --- rapor
    say = Counter(a for a, _, _ in bulgular)
    print(f"\n{len(sayfalar)} sayfa, {gorsel_sayisi} görsel etiketi denetlendi")
    print(f"YUKSEK {say['YUKSEK']} · ORTA {say['ORTA']} · DUSUK {say['DUSUK']}")

    for agirlik in ("YUKSEK", "ORTA", "DUSUK"):
        kume = [(s, m) for a, s, m in bulgular if a == agirlik]
        if not kume:
            continue
        print(f"\n--- {agirlik} ({len(kume)}) ---")
        ozet: Counter[str] = Counter()
        ornek: dict[str, str] = {}
        for s, m in kume:
            anahtar = re.sub(r"[^a-zA-ZçğıöşüÇĞİÖŞÜ ]+", "", m)[:52]
            ozet[anahtar] += 1
            ornek.setdefault(anahtar, f"{s} — {m}")
        for anahtar, n in ozet.most_common(20):
            print(f"  {n:4}x {ornek[anahtar][:150]}")

    return 1 if say["YUKSEK"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
