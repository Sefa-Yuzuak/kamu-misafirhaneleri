"""HTML parçaları: ikon takımı, sayfa iskeleti, kartlar, düğmeler."""
from __future__ import annotations
import html
import json
import re
from stil import KRITIK
from veri import TURLER, kisa_ad, slug, tesis_slug
SITE = "https://kamumisafirhaneler.com"
# derle.py karma adlı dosyayı üretince bunu günceller
STIL_YOLU = "/static/s.css"
AD = "Kamu Misafirhaneleri"
def e(x) -> str:
    return html.escape(str(x or ""), quote=True)
# --------------------------------------------------------------------------
# İkonlar — hepsi tek renk (currentColor), 24x24 çizgi, kalınlık CSS'ten.
# --------------------------------------------------------------------------
IKONLAR = {
    "telefon": "M6.6 3H4a1 1 0 0 0-1 1.1A16.9 16.9 0 0 0 19.9 21a1 1 0 0 0 1.1-1v-2.6a1 1 0 0 0-.8-1l-3-.6a1 1 0 0 0-1 .4l-1 1.3a13.4 13.4 0 0 1-5.7-5.7l1.3-1a1 1 0 0 0 .4-1l-.6-3a1 1 0 0 0-1-.8Z",
    "whatsapp": "M3.5 20.5 5 16.3A8 8 0 1 1 7.9 19.2l-4.4 1.3ZM9 9.3c.2 1 .8 2.2 1.7 3.1.9.9 2 1.5 3 1.7.4 0 .8-.1 1-.4l.6-.7a.6.6 0 0 1 .7-.1l1.6.8c.2.1.3.4.3.6-.1.7-.6 1.4-1.4 1.6-2.1.5-5-1.2-6.6-2.8C8.3 11.5 6.6 8.6 7.1 6.5c.2-.8.9-1.3 1.6-1.4.2 0 .5.1.6.3l.8 1.6c.1.2 0 .5-.1.7l-.7.6c-.3.2-.4.6-.3 1Z",
    "yol": "M21.4 11.1 12.9 2.6a1.3 1.3 0 0 0-1.8 0l-8.5 8.5a1.3 1.3 0 0 0 0 1.8l8.5 8.5c.5.5 1.3.5 1.8 0l8.5-8.5c.5-.5.5-1.3 0-1.8ZM9.5 14.5v-2.6a1.4 1.4 0 0 1 1.4-1.4h4M12.6 8.3l2.3 2.2-2.3 2.2",
    "mail": "M3 7.5A2.5 2.5 0 0 1 5.5 5h13A2.5 2.5 0 0 1 21 7.5v9a2.5 2.5 0 0 1-2.5 2.5h-13A2.5 2.5 0 0 1 3 16.5v-9ZM3.4 7l7.5 5.3c.7.5 1.5.5 2.2 0L20.6 7",
    "konum": "M20 10.4c0 5.2-6.6 10.3-7.6 11a.7.7 0 0 1-.8 0C10.6 20.7 4 15.6 4 10.4a8 8 0 0 1 16 0ZM14.7 10.3a2.7 2.7 0 1 1-5.4 0 2.7 2.7 0 0 1 5.4 0Z",
    "deniz": "M2 17.2c1.7 0 1.7 1.6 3.3 1.6s1.7-1.6 3.4-1.6 1.7 1.6 3.3 1.6 1.7-1.6 3.3-1.6 1.7 1.6 3.4 1.6 1.6-1.6 3.3-1.6M2 12.4c1.7 0 1.7 1.6 3.3 1.6s1.7-1.6 3.4-1.6 1.7 1.6 3.3 1.6 1.7-1.6 3.3-1.6 1.7 1.6 3.4 1.6 1.6-1.6 3.3-1.6M2 7.6c1.7 0 1.7 1.6 3.3 1.6S7 7.6 8.7 7.6s1.7 1.6 3.3 1.6 1.7-1.6 3.3-1.6 1.7 1.6 3.4 1.6S20.3 7.6 22 7.6",
    "okul": "M3 9.2 12 4.5l9 4.7-9 4.7-9-4.7ZM6.6 11.1v5.3c0 .5.3 1 .8 1.2a10.6 10.6 0 0 0 9.2 0c.5-.2.8-.7.8-1.2v-5.3M20.6 10v5.4",
    "kalkan": "M12 3.2 5 5.9v5.7c0 4 3 7.7 7 9.2 4-1.5 7-5.2 7-9.2V5.9l-7-2.7ZM9.5 12.1l1.9 1.9 3.4-3.6",
    "bina": "M4.5 21V4.7c0-1 .8-1.7 1.8-1.7h6.4c1 0 1.8.8 1.8 1.7V21M14.5 9.6h3.4c1 0 1.6.7 1.6 1.6V21M3 21h18M8 7.2h3M8 11.2h3M8 15.2h3M17 13.5v.1M17 17.4v.1",
    "bayrak": "M5 21V4M5 4.5h11.2c.7 0 1.1.8.7 1.4l-2.3 3.3c-.2.3-.2.7 0 1l2.3 3.3c.4.6 0 1.4-.7 1.4H5",
    "ara": "M17.5 17.5 21 21M19.5 11.2a8.2 8.2 0 1 1-16.5 0 8.2 8.2 0 0 1 16.5 0Z",
    "yatak": "M3 18v-6.6h18V18M3 11.4V6M21 18v1.6M3 18v1.6M6.4 11.4V9.2c0-.6.5-1.1 1.1-1.1h3c.6 0 1.1.5 1.1 1.1v2.2M12.4 11.4V9.2c0-.6.5-1.1 1.1-1.1h3c.6 0 1.1.5 1.1 1.1v2.2",
    "havuz": "M2 18.5c1.6 0 1.6 1.4 3.2 1.4s1.6-1.4 3.2-1.4 1.6 1.4 3.2 1.4 1.6-1.4 3.2-1.4 1.6 1.4 3.2 1.4 1.6-1.4 3.2-1.4M7 16.5V6.2A2.2 2.2 0 0 1 9.2 4c1.2 0 2.2 1 2.2 2.2M17 16.5V6.2A2.2 2.2 0 0 0 14.8 4c-1.2 0-2.2 1-2.2 2.2M7 9.4h10M7 13h10",
    "kahvalti": "M17 8h1.6a2.7 2.7 0 0 1 0 5.4H17M3.5 8h13.4v5c0 2.8-2.3 5.1-5.1 5.1H8.6A5.1 5.1 0 0 1 3.5 13V8ZM3 21.2h15",
    "restoran": "M6.5 3v7.2a2.5 2.5 0 0 0 5 0V3M9 10.5V21M17.5 3c-1.4 1-2.3 2.7-2.3 4.6v4.2h4.3M19.5 11.8V21",
    "wifi": "M5.3 12.4a9.5 9.5 0 0 1 13.4 0M2.4 9.2a13.6 13.6 0 0 1 19.2 0M8.4 15.7a5.1 5.1 0 0 1 7.2 0M12 19.3v.1",
    "otopark": "M5.5 16.5v2.1a.9.9 0 0 1-.9.9H3.9a.9.9 0 0 1-.9-.9v-2.1M21 16.5v2.1a.9.9 0 0 1-.9.9h-.7a.9.9 0 0 1-.9-.9v-2.1M3 16.4v-3.6l2-5c.3-.7.9-1.1 1.6-1.1h10.8c.7 0 1.3.4 1.6 1.1l2 5v3.6ZM3.2 12.8h17.6M6.6 14.6h.1M17.4 14.6h.1",
    "klima": "M3 5.6c0-.9.7-1.6 1.6-1.6h14.8c.9 0 1.6.7 1.6 1.6v4.8c0 .9-.7 1.6-1.6 1.6H4.6c-.9 0-1.6-.7-1.6-1.6ZM6.4 8.2h11.2M7 15.4c0 1.4-.6 2.2-1.6 3M12 15.4c0 1.6 0 2.4-1 3.4M17 15.4c0 1.4.6 2.2 1.6 3",
    "cocuk": "M12 8.6a2.8 2.8 0 1 0 0-5.6 2.8 2.8 0 0 0 0 5.6ZM12 8.6V15M8 11.4h8M9.5 21l2.5-6 2.5 6",
    "manzara": "M3 18.5 8.6 9.7l4 5.6 2.4-3 6 6.2ZM17.2 7.6a1.6 1.6 0 1 1-3.2 0 1.6 1.6 0 0 1 3.2 0Z",
    "saat": "M12 6.8V12l3.2 1.9M21 12a9 9 0 1 1-18 0 9 9 0 0 1 18 0Z",
    "para": "M3 7.4c0-.9.7-1.6 1.6-1.6h14.8c.9 0 1.6.7 1.6 1.6v9.2c0 .9-.7 1.6-1.6 1.6H4.6c-.9 0-1.6-.7-1.6-1.6ZM14.6 12a2.6 2.6 0 1 1-5.2 0 2.6 2.6 0 0 1 5.2 0ZM6.4 9.6v4.8M17.6 9.6v4.8",
    "bilgi": "M12 16v-4.4M12 8.3v.1M21 12a9 9 0 1 1-18 0 9 9 0 0 1 18 0Z",
    "uyari": "M12 9.6V14M12 17.3v.1M10.3 4.2 2.7 17.4A2 2 0 0 0 4.4 20.4h15.2a2 2 0 0 0 1.7-3L13.7 4.2a2 2 0 0 0-3.4 0Z",
    "bos": "M3 13.5h4.6l1.4 2.4h6l1.4-2.4H21M3 13.5 5.8 6c.3-.8 1-1.3 1.9-1.3h8.6c.9 0 1.6.5 1.9 1.3L21 13.5v4.3c0 .9-.7 1.6-1.6 1.6H4.6c-.9 0-1.6-.7-1.6-1.6Z",
    "dis": "M14.5 4.5H19a.5.5 0 0 1 .5.5v4.5M19.2 4.8 12 12M17.5 14v4.4c0 .9-.7 1.6-1.6 1.6H5.6c-.9 0-1.6-.7-1.6-1.6V8.1c0-.9.7-1.6 1.6-1.6H10",
    "ok": "M5 12h13M13 6.6 18.6 12 13 17.4",
    "harita": "M9 4.4 3.6 6.6c-.4.2-.6.5-.6.9v11.3c0 .6.6 1 1.1.8L9 17.6M9 4.4v13.2M9 4.4l6 2.2M15 6.6v13.2M15 6.6l5.4-2.2c.5-.2 1.1.2 1.1.8v11.3c0 .4-.2.7-.6.9L15 19.8M15 19.8 9 17.6",
    "kalp": "M12 6.6a4.6 4.6 0 0 1 7.9 3.2c0 4-6 8.2-7.9 9.6-1.9-1.4-7.9-5.6-7.9-9.6A4.6 4.6 0 0 1 12 6.6Z",
    "yildiz": "m12 3.5 2.6 5.4 5.9.8-4.3 4.2 1 5.9-5.2-2.8-5.2 2.8 1-5.9L3.5 9.7l5.9-.8Z",
    "kurum": "M12 3.2 3 7.8h18ZM5.4 10.4v6.9M9.8 10.4v6.9M14.2 10.4v6.9M18.6 10.4v6.9M3.4 20.4h17.2",
}
def ik(ad: str, sinif: str = "ik") -> str:
    d = IKONLAR[ad]
    return (
        f'<svg class="{sinif}" viewBox="0 0 24 24" aria-hidden="true" focusable="false">'
        f'<path d="{d}"/></svg>'
    )
# --------------------------------------------------------------------------
# Olanak metninden ikon çıkarma
# --------------------------------------------------------------------------
_OLANAK = [
    (r"çocuk havuz", "havuz", "Çocuk havuzu"),
    (r"havuz", "havuz", "Havuz"),
    (r"deniz manzara|manzaral", "manzara", "Deniz manzarası"),
    (r"plaj|sahil|denize", "deniz", "Sahil"),
    (r"kahvalt", "kahvalti", "Kahvaltı"),
    (r"restoran|lokanta|yemek", "restoran", "Restoran"),
    (r"otopark|park yeri", "otopark", "Otopark"),
    (r"wifi|wi-fi|internet|kablosuz", "wifi", "Kablosuz internet"),
    (r"klima", "klima", "Klima"),
    (r"çocuk (oyun|park)|oyun alan", "cocuk", "Çocuk oyun alanı"),
    (r"(\d+)\s*oda", "yatak", None),
    (r"(\d+)\s*yatak", "yatak", None),
    (r"toplantı|konferans", "bina", "Toplantı salonu"),
]
def olanak_ikonlari(olanaklar: list[str] | None) -> list[tuple[str, str]]:
    """Serbest metin olanakları (ikon, etiket) çiftlerine çevirir."""
    if not olanaklar:
        return []
    cikti: list[tuple[str, str]] = []
    goruldu: set[str] = set()
    for ham in olanaklar:
        alt = ham.lower()
        eslesti = False
        for kalip, ikon, etiket in _OLANAK:
            if re.search(kalip, alt):
                metin = etiket or ham.strip()
                if metin.lower() in goruldu:
                    eslesti = True
                    break
                goruldu.add(metin.lower())
                cikti.append((ikon, metin[0].upper() + metin[1:]))
                eslesti = True
                break
        if not eslesti and len(ham) < 40:
            if ham.lower() not in goruldu:
                goruldu.add(ham.lower())
                cikti.append(("bilgi", ham[0].upper() + ham[1:]))
    return cikti
# --------------------------------------------------------------------------
# İletişim düğmeleri
# --------------------------------------------------------------------------
def _rakam(no: str) -> str:
    d = re.sub(r"\D", "", no)
    return d[1:] if d.startswith("0") else d
def cep_mi(no: str) -> bool:
    return _rakam(no).startswith("5")
def yol_tarifi_url(t: dict) -> str:
    hedef = f"{t['ad']} {t['ilce']} {t['il']}"
    import urllib.parse
    return "https://www.google.com/maps/dir/?api=1&destination=" + urllib.parse.quote(hedef)
def google_yer_url(t: dict) -> str:
    """Tesisin Google Haritalar kaydı — yorumlar orada okunur."""
    import urllib.parse
    return "https://www.google.com/maps/search/?api=1&query=" + urllib.parse.quote(
        f"{t['ad']} {t['ilce']} {t['il']}"
    )
def osm_adres(konum: dict | None) -> str:
    """OSM display_name'den okunur bir sokak adresi çıkarır.
    Yalnızca tesis olarak eşleşen kayıtlarda anlamlıdır; ilçe merkezlerinde boş döner.
    """
    if not konum or konum.get("kesinlik") != "tesis":
        return ""
    parcalar = [x.strip() for x in (konum.get("osm") or "").split(",")]
    if len(parcalar) < 3:
        return ""
    # ilk öğe tesis adı; sokak/cadde ve mahalleyi al
    govde, goruldu = [], set()
    for x in parcalar[1:4]:
        a = x.lower()
        if a and a not in goruldu and not a.isdigit():
            goruldu.add(a)
            govde.append(x)
    return ", ".join(govde)
def wa_url(t: dict, no: str) -> str:
    import urllib.parse
    mesaj = (
        f"Merhaba, {t['ad']} için müsaitlik ve fiyat bilgisi almak istiyorum. "
        "(kamumisafirhaneler.com üzerinden ulaşıyorum)"
    )
    return f"https://wa.me/9{_rakam(no)}?text=" + urllib.parse.quote(mesaj)
def eylemler(t: dict, buyuk: bool = False) -> str:
    """Ara / WhatsApp / Yol tarifi / E-posta düğmeleri."""
    sinif = "dg" if buyuk else "dg dg-sm"
    tel = (t.get("telefon") or [None])[0]
    cep = next((n for n in (t.get("telefon") or []) if cep_mi(n)), None)
    p = []
    if tel:
        p.append(
            f'<a class="{sinif} dg-1" href="tel:+9{_rakam(tel)}" '
            f'aria-label="{e(tel) if buyuk else "Ara"}'
            f' — {e(kisa_ad(t["ad"]))} telefonla ara">{ik("telefon")}'
            f'<span>{e(tel) if buyuk else "Ara"}</span></a>'
        )
    if cep:
        p.append(
            f'<a class="{sinif} dg-2" href="{e(wa_url(t, cep))}" target="_blank" rel="noopener nofollow" '
            f'aria-label="WhatsApp ile yaz">{ik("whatsapp")}<span>WhatsApp</span></a>'
        )
    p.append(
        f'<a class="{sinif} dg-2" href="{e(yol_tarifi_url(t))}" target="_blank" rel="noopener nofollow" '
        f'aria-label="{e(t["ad"])} yol tarifi">{ik("yol")}<span>Yol tarifi</span></a>'
    )
    if t.get("eposta"):
        p.append(
            f'<a class="{sinif} dg-2" href="mailto:{e(t["eposta"])}'
            f'?subject={e("Musaitlik ve fiyat bilgisi")}" '
            f'aria-label="E-posta gönder">{ik("mail")}<span>E-posta</span></a>'
        )
    return "".join(p)
# --------------------------------------------------------------------------
# Kartlar
# --------------------------------------------------------------------------
def tesis_karti(t: dict, gorseller: dict, il_goster: bool = True) -> str:
    g = gorseller.get(t["il"])
    s = tesis_slug(t)
    ikon = TURLER[t["tur"]][2]
    kisa_tur = TURLER[t["tur"]][1]
    if g:
        gorsel = (
            f'<img src="/img/il/{g["sm"]}" '
            f'srcset="/img/il/{g["sm"]} 640w, /img/il/{g.get("md", g["lg"])} 800w, '
            f'/img/il/{g["lg"]} 1200w" '
            f'sizes="(max-width:520px) 92vw, (max-width:900px) 44vw, 300px" '
            f'width="640" height="360" loading="lazy" decoding="async" '
            f'alt="{e(t["il"])} — tesis bu ilde yer alıyor">'
        )
    else:
        gorsel = ""
    rozetler = f'<span class="rz rz-tur">{ik(ikon)}{e(kisa_tur)}</span>'
    if t.get("deniz"):
        rozetler += f'<span class="rz rz-deniz">{ik("deniz")}Sahilde</span>'
    olanak = olanak_ikonlari(t.get("olanaklar"))[:4]
    ol_html = ""
    if olanak:
        ol_html = '<ul class="ol">' + "".join(
            f"<li>{ik(i)}{e(m)}</li>" for i, m in olanak
        ) + "</ul>"
    meta = [f'{ik("konum")}{e(t["ilce"])}' + (f", {e(t['il'])}" if il_goster else "")]
    if t.get("ankara_saat"):
        meta.append(f'{ik("saat")}Ankara {e(t["ankara_saat"])} sa')
    fiyat = ""
    if t.get("fiyat_2026"):
        kisa = t["fiyat_2026"].split(";")[0].strip()
        fiyat = f'<p class="tk-fiyat">{ik("para")} {e(kisa)}</p>'
    return f"""<article class="tk">
<div class="tk-gorsel">{gorsel}<span class="rzs-k">{rozetler}</span><span class="yer-et">{ik("konum")}{e(t["il"])}</span></div>
<div class="tk-govde">
<h3 class="tk-ad"><a href="/tesis/{s}/">{e(kisa_ad(t["ad"]))}</a></h3>
<p class="tk-meta">{"".join(f"<span>{m}</span>" for m in meta)}</p>
{fiyat}{ol_html}</div>
<div class="tk-alt">{eylemler(t)}</div>
</article>"""
def il_karti(il: str, sayi: int, deniz_sayi: int, gorseller: dict) -> str:
    g = gorseller.get(il)
    s = slug(il)
    gorsel = (
        f'<img src="/img/il/{g["sm"]}" '
        f'srcset="/img/il/{g["sm"]} 640w, /img/il/{g.get("md", g["lg"])} 800w" '
        f'sizes="(max-width:520px) 44vw, 210px" '
        f'width="640" height="360" loading="lazy" decoding="async" '
        f'alt="{e(il)} ilinden bir görünüm">'
        if g
        else ""
    )
    nk = (
        f'<span class="deniz-nk">{ik("deniz")}{deniz_sayi}</span>' if deniz_sayi else ""
    )
    return (
        f'<a class="il-k" href="/il/{s}/">{gorsel}{nk}'
        f'<span class="yz"><strong>{e(il)}</strong>'
        f'<span>{sayi} tesis</span></span></a>'
    )
# --------------------------------------------------------------------------
# Sayfa iskeleti
# --------------------------------------------------------------------------
GEZ = [
    ("/il/", "İller"),
    ("/harita/", "Harita"),
    ("/araclar/", "Araçlar"),
    ("/liste/", "Listeler"),
    ("/deniz/", "Denize yakın"),
    ("/tur/ogretmenevleri/", "Öğretmenevleri"),
    ("/rehber/", "Rehber"),
]
HARITA_ON = (
    '<link rel="preconnect" href="https://tile.openstreetmap.org" crossorigin>'
    '<link rel="dns-prefetch" href="https://tile.openstreetmap.org">'
) + "".join(
    f'<link rel="preload" href="/static/harita/{ad}" as="style" '
    "onload=\"this.rel='stylesheet'\">"
    for ad in ("leaflet.css", "markercluster.css", "markercluster-default.css")
)


NOSCRIPT_GEZ = (
    "<noscript><style>.gez-dg{display:none!important}"
    "@media(max-width:1000px){.gez{position:static!important;display:flex!important;"
    "flex-direction:row!important;overflow-x:auto;background:none!important;"
    "border:0!important;box-shadow:none!important;padding:0!important}}</style></noscript>"
)
MARKA_SVG = (
    '<svg viewBox="0 0 32 32" fill="none" aria-hidden="true">'
    '<rect x="1.2" y="1.2" width="29.6" height="29.6" rx="8" fill="var(--vurgu)"/>'
    '<path d="M8 22.5V13l8-4.6 8 4.6v9.5" stroke="#fff" stroke-width="2" '
    'stroke-linecap="round" stroke-linejoin="round"/>'
    '<path d="M13 22.5v-4.8h6v4.8" stroke="#fff" stroke-width="2" '
    'stroke-linecap="round" stroke-linejoin="round"/>'
    '<path d="M6 22.6h20" stroke="#fff" stroke-width="2" stroke-linecap="round"/></svg>'
)
def kabuk(
    *,
    baslik: str,
    aciklama: str,
    yol: str,
    icerik: str,
    jsonld: list[dict] | None = None,
    og_gorsel: str | None = None,
    kirintilar: list[tuple[str, str]] | None = None,
    aktif: str = "",
    ek_bas: str = "",
    on_gorsel: str = "",
    harita: bool = False,
    arac: bool = False,
) -> str:
    kanonik = SITE + yol
    ld = "".join(
        f'<script type="application/ld+json">{json.dumps(x, ensure_ascii=False, separators=(",", ":"))}</script>'
        for x in (jsonld or [])
    )
    og = og_gorsel or "/img/og.png"
    gez = "".join(
        f'<a href="{u}"{" aria-current=\"page\"" if u == aktif else ""}>{a}</a>'
        for u, a in GEZ
    )
    krnt = ""
    if kirintilar:
        parcalar = []
        for i, (u, a) in enumerate(kirintilar):
            son = i == len(kirintilar) - 1
            parcalar.append(f"<span>›</span>" if i else "")
            parcalar.append(a if son else f'<a href="{u}">{a}</a>')
        krnt = f'<nav class="kap krnt" aria-label="Sayfa yolu">{"".join(parcalar)}</nav>'
    return f"""<!doctype html>
<html lang="tr">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{e(baslik)}</title>
<meta name="description" content="{e(aciklama)}">
<link rel="canonical" href="{kanonik}">
<meta property="og:type" content="website">
<meta property="og:site_name" content="{AD}">
<meta property="og:locale" content="tr_TR">
<meta property="og:title" content="{e(baslik)}">
<meta property="og:description" content="{e(aciklama)}">
<meta property="og:url" content="{kanonik}">
<meta property="og:image" content="{SITE}{og}">
<meta name="twitter:card" content="summary_large_image">
<meta name="theme-color" content="#0D5C4E" media="(prefers-color-scheme:light)">
<meta name="theme-color" content="#0F1413" media="(prefers-color-scheme:dark)">
<link rel="icon" href="/favicon.svg" type="image/svg+xml">
<link rel="preload" href="/static/f/newsreader-latin-ext-600-normal.woff2" as="font" type="font/woff2" crossorigin>
<style>{KRITIK}</style>
<link rel="preload" href="{STIL_YOLU}" as="style" onload="this.rel='stylesheet'">
<noscript><link rel="stylesheet" href="{STIL_YOLU}"></noscript>
{HARITA_ON if harita else ""}
{NOSCRIPT_GEZ}
{f'<link rel="preload" as="image" href="{on_gorsel}" fetchpriority="high">' if on_gorsel else ''}{ek_bas}{ld}</head>
<body>
<a class="atla" href="#ana">İçeriğe atla</a>
<header class="ust">
<div class="kap">
<a class="marka" href="/">{MARKA_SVG}<b>Kamu</b><span>Misafirhaneleri</span></a>
<button class="gez-dg" id="gez-dg" aria-expanded="false" aria-controls="gez"
aria-label="Menüyü aç"><span class="gez-cizgi"></span>Menü</button>
<nav class="gez" id="gez" aria-label="Ana menü">{gez}</nav>
</div>
</header>
{krnt}
<main id="ana">
{icerik}
</main>
<footer class="alt">
<div class="kap">
<div class="alt-iz">
<div>
<h3>{AD}</h3>
<p>Türkiye'nin 81 ilindeki öğretmenevi, polisevi, üniversite ve bakanlık
misafirhanelerinin bağımsız dizini. Rezervasyon alınmaz; her tesis doğrudan aranır.</p>
</div>
<div><h3>Keşfet</h3><ul>
<li><a href="/il/">81 il</a></li>
<li><a href="/harita/">Harita</a></li>
<li><a href="/ara/">Tesis ara</a></li>
<li><a href="/liste/">Sıralı listeler</a></li>
<li><a href="/deniz/">Denize yakın tesisler</a></li>
<li><a href="/tur/ogretmenevleri/">Öğretmenevleri</a></li>
<li><a href="/tur/polisevleri/">Polisevleri</a></li>
<li><a href="/tur/universite-misafirhaneleri/">Üniversite misafirhaneleri</a></li>
</ul></div>
<div><h3>Araçlar</h3><ul>
<li><a href="/araclar/en-yakin/">Bana en yakın tesis</a></li>
<li><a href="/araclar/tatil-butcesi/">Tatil bütçesi</a></li>
<li><a href="/araclar/mesafe/">Mesafe ve süre</a></li>
<li><a href="/araclar/karsilastir/">Tesis karşılaştır</a></li>
</ul></div>
<div><h3>Rehber</h3><ul>
<li><a href="/rehber/ogretmenevinde-kimler-kalabilir/">Kimler kalabilir?</a></li>
<li><a href="/rehber/ogretmenevi-fiyatlari/">2026 fiyatları</a></li>
<li><a href="/rehber/denize-sifir-kamu-tesisleri/">Denize sıfır tesisler</a></li>
<li><a href="/rehber/rezervasyon-nasil-yapilir/">Rezervasyon nasıl yapılır?</a></li>
<li><a href="/rehber/ankaraya-yakin-deniz-tatili/">Ankara'ya yakın deniz</a></li>
</ul></div>
<div><h3>Veri</h3><ul>
<li><a href="/tesisler.json">Açık veri (JSON)</a></li>
<li><a href="/sitemap.xml">Site haritası</a></li>
<li><a href="/kaynaklar/">Kaynaklar ve katkı</a></li>
</ul></div>
</div>
<div class="alt-son">
<span>Bağımsız dizindir; hiçbir kuruma ait değildir ve rezervasyon almaz.</span>
<span>Fotoğraflar Wikimedia Commons, ilgili lisanslarıyla.</span>
</div>
</div>
</footer>
<script src="/static/a.js" defer></script>
{'<script src="/static/t.js" defer></script>' if arac else ""}
{'<script src="/static/harita/leaflet.js" defer></script><script src="/static/harita/markercluster.js" defer></script><script src="/static/h.js" defer></script>' if harita else ""}
</body>
</html>"""
# --------------------------------------------------------------------------
# Harita bileşeni
# --------------------------------------------------------------------------
HARITA_ACIKLAMA = (
    "Tesislerin bir kısmı OpenStreetMap'te kayıtlı; kalanlar için ilçe merkezi "
    "gösterilir. Tam adres için tesisi arayın."
)
def harita_kutusu(*, ozellikler: str, sinif: str = "", aciklama: bool = True,
                  say_kimlik: bool = False) -> str:
    """#harita kabı + gösterge. `ozellikler` data-* niteliklerini taşır."""
    gosterge = (
        f'<div class="harita-alt">'
        f'<span class="im"><span class="nk nk-tesis"></span>Tesis konumu</span>'
        f'<span class="im"><span class="nk nk-deniz"></span>Denize yakın</span>'
        f'<span class="im"><span class="nk nk-ilce"></span>İlçe merkezi (yaklaşık)</span>'
        + (f'<span class="im" id="harita-say" style="margin-left:auto"></span>'
           if say_kimlik else "")
        + "</div>"
        if aciklama else ""
    )
    return (
        f'<div class="harita-sar {sinif}"><div id="harita" {ozellikler}></div>'
        f"{gosterge}</div>"
    )