"""Yazı tipi alt kümeleme: latin-ext dosyalarını sayfada geçen harflere indirir.

Ölçüm (29.08.2026, Lighthouse ağ dökümü): bir tesis sayfasında 10 woff2
dosyası, toplam 274 KiB — sayfa ağırlığının %42'si. Bunun 155 KiB'ı latin-ext
alt kümeleri ve içlerinden yalnızca beş harf kullanılıyor: ğ Ğ ş Ş İ.
(ı zaten latin alt kümesinde tanımlı, latin-ext gerektirmiyor.)

Bu yüzden latin-ext dosyaları, üretilen sayfalarda o aralığa gerçekten düşen
kod noktalarına indirgeniyor. Kaynak dosyalar (static/f) tam hâlde kalır;
alt kümeleme yalnızca çıktıya (site/static/f) uygulanır, böylece ileride
içerik yeni bir harf getirirse yeniden üretilebilir.
"""

from __future__ import annotations

import re
from pathlib import Path

#: CSS'teki latin-ext unicode-range'i (s.css @font-face bloklarıyla birebir)
LATIN_EXT = [
    (0x0100, 0x02BA), (0x02BD, 0x02C5), (0x02C7, 0x02CC), (0x02CE, 0x02D7),
    (0x02DD, 0x02FF), (0x0304, 0x0304), (0x0308, 0x0308), (0x0329, 0x0329),
    (0x1D00, 0x1DBF), (0x1E00, 0x1E9F), (0x1EF2, 0x1EFF), (0x2020, 0x2020),
    (0x20A0, 0x20AB), (0x20AD, 0x20C0), (0x2113, 0x2113), (0x2C60, 0x2C7F),
    (0xA720, 0xA7FF),
]

_ETIKET = re.compile(r"<[^>]+>")


def _aralikta(kod: int) -> bool:
    return any(a <= kod <= b for a, b in LATIN_EXT)


def kullanilan_kodlar(site: Path) -> set[int]:
    """Üretilmiş sayfalarda latin-ext aralığına düşen kod noktaları."""
    kodlar: set[int] = set()
    for dosya in site.rglob("*.html"):
        for karakter in dosya.read_text("utf-8"):
            kod = ord(karakter)
            if kod > 0xFF and _aralikta(kod):
                kodlar.add(kod)
    return kodlar


def alt_kumele(kaynak: Path, hedef: Path, kodlar: set[int]) -> tuple[int, int]:
    """Tek dosyayı verilen kod noktalarına indirger; (önce, sonra) bayt."""
    from fontTools import subset

    onceki = kaynak.stat().st_size
    secenekler = subset.Options()
    secenekler.flavor = "woff2"
    secenekler.desubroutinize = True
    secenekler.layout_features = ["*"]
    secenekler.notdef_outline = True

    font = subset.load_font(str(kaynak), secenekler)
    alt = subset.Subsetter(options=secenekler)
    alt.populate(unicodes=kodlar)
    alt.subset(font)
    subset.save_font(font, str(hedef), secenekler)
    font.close()
    return onceki, hedef.stat().st_size


def uygula(kok: Path, cikti: Path) -> None:
    """site/static/f içindeki latin-ext dosyalarını yerinde küçültür."""
    hedef_dizin = cikti / "static" / "f"
    if not hedef_dizin.exists():
        return
    kodlar = kullanilan_kodlar(cikti)
    if not kodlar:
        return

    onceki_toplam = sonraki_toplam = 0
    sayi = 0
    for dosya in sorted(hedef_dizin.glob("*latin-ext*.woff2")):
        kaynak = kok / "static" / "f" / dosya.name
        if not kaynak.exists():
            continue
        try:
            onceki, sonraki = alt_kumele(kaynak, dosya, kodlar)
        except Exception as hata:  # alt kümeleme yapılamazsa tam dosya kalır
            print(f"  yazi tipi atlandi ({dosya.name}): {type(hata).__name__} {hata}")
            continue
        onceki_toplam += onceki
        sonraki_toplam += sonraki
        sayi += 1

    if sayi:
        # Harflerin kendisi yazdirilmiyor: Windows konsolu (cp1254) bir
        # kismini kodlayamiyor ve derleme cokuyordu. Kod noktasi guvenli.
        ornek = " ".join(f"U+{k:04X}" for k in sorted(kodlar)[:8])
        print(
            f"yazı tipi: {sayi} latin-ext dosyası "
            f"{onceki_toplam // 1024} KB -> {sonraki_toplam // 1024} KB "
            f"({len(kodlar)} kod noktası: {ornek}"
            + (" …" if len(kodlar) > 8 else "")
            + ")"
        )
