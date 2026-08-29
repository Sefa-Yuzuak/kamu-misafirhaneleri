"""Dağıtım katmanı: besleme, IndexNow, tarayıcı arama tanımı, alıntı sayfası.

Not: satın alınan ya da toplu üretilen bağlantı, Google'ın bağlantı spamı
politikasına aykırıdır ve siteyi cezalandırır. Buradaki her şey meşru yoldan
bulunurluk artırır: içeriği aramaya bildirmek, besleme sunmak ve veriyi
başkalarının kaynak göstererek kullanabileceği hale getirmek.
"""

from __future__ import annotations

import hashlib
from datetime import datetime, timezone

from parca import AD, SITE, e, ik, kabuk

# IndexNow anahtarı alan adından türetilir: her derlemede aynı kalır,
# gizli bir bilgi değildir, zaten site kökünde yayımlanır.
INDEXNOW_ANAHTAR = hashlib.sha256(
    b"kamumisafirhaneler.com/indexnow"
).hexdigest()[:32]

INDEXNOW_SUNUCULARI = [
    "https://api.indexnow.org/indexnow",
    "https://www.bing.com/indexnow",
    "https://yandex.com/indexnow",
]


def rss(sayfalar: list[tuple[str, str, str]], guncelleme: datetime) -> str:
    """sayfalar: [(yol, başlık, açıklama), ...]"""
    tarih = guncelleme.strftime("%a, %d %b %Y %H:%M:%S +0000")
    ogeler = "".join(
        f"<item><title>{e(baslik)}</title>"
        f"<link>{SITE}{yol}</link>"
        f"<guid isPermaLink=\"true\">{SITE}{yol}</guid>"
        f"<description>{e(aciklama)}</description>"
        f"<pubDate>{tarih}</pubDate></item>"
        for yol, baslik, aciklama in sayfalar
    )
    return (
        '<?xml version="1.0" encoding="UTF-8"?>'
        '<rss version="2.0" xmlns:atom="http://www.w3.org/2005/Atom"><channel>'
        f"<title>{AD}</title>"
        f"<link>{SITE}/</link>"
        "<description>Türkiye'nin 81 ilindeki kamu konaklama tesislerinin "
        "bağımsız dizini: öğretmenevi, polisevi, üniversite ve bakanlık "
        "misafirhaneleri.</description>"
        "<language>tr</language>"
        f"<lastBuildDate>{tarih}</lastBuildDate>"
        f'<atom:link href="{SITE}/feed.xml" rel="self" type="application/rss+xml"/>'
        f"{ogeler}</channel></rss>"
    )


def opensearch() -> str:
    return (
        '<?xml version="1.0" encoding="UTF-8"?>'
        '<OpenSearchDescription xmlns="http://a9.com/-/spec/opensearch/1.1/">'
        f"<ShortName>{AD}</ShortName>"
        "<Description>562 kamu konaklama tesisi içinde ara</Description>"
        "<InputEncoding>UTF-8</InputEncoding>"
        f'<Image width="16" height="16" type="image/svg+xml">{SITE}/favicon.svg</Image>'
        f'<Url type="text/html" method="get" template="{SITE}/ara/?q={{searchTerms}}"/>'
        f'<moz:SearchForm xmlns:moz="http://www.mozilla.org/2006/browser/search/">'
        f"{SITE}/ara/</moz:SearchForm>"
        "</OpenSearchDescription>"
    )


def manifest() -> str:
    import json

    return json.dumps(
        {
            "name": AD,
            "short_name": "Kamu Misafirhaneleri",
            "description": "81 ilde 562 öğretmenevi, polisevi ve kamu misafirhanesi.",
            "start_url": "/",
            "scope": "/",
            "display": "standalone",
            "lang": "tr",
            "background_color": "#FBF9F5",
            "theme_color": "#0D5C4E",
            "icons": [
                {"src": "/favicon.svg", "sizes": "any", "type": "image/svg+xml"},
                {"src": "/img/og.png", "sizes": "1200x630", "type": "image/png"},
            ],
        },
        ensure_ascii=False,
        separators=(",", ":"),
    )


def veri_sayfasi(tesisler: list[dict], toplam_sayfa: int, tarih: str) -> str:
    from uret import kirinti_ld, sss_html, sss_ld

    kirintilar = [("/", "Ana sayfa"), ("/veri/", "Açık veri")]
    deniz = sum(1 for t in tesisler if t.get("deniz"))
    fiyatli = sum(1 for t in tesisler if t.get("fiyat_2026"))
    telefonlu = sum(1 for t in tesisler if t.get("telefon"))

    alinti_metin = (
        f'Kamu Misafirhaneleri (2026). Türkiye kamu konaklama tesisleri veri kümesi. '
        f'{SITE}/tesisler.json (Erişim: {tarih})'
    )
    gomme = (
        f'<a href="{SITE}/" rel="noopener">Kamu Misafirhaneleri</a> — '
        f'81 ilde {len(tesisler)} öğretmenevi, polisevi ve kamu misafirhanesi'
    )

    sss = [
        ("Bu veriyi kendi sitemde kullanabilir miyim?",
         "Evet. Veri kümesi CC BY 4.0 ile açıktır: ticari kullanım dahil serbesttir, "
         "tek koşul kaynak göstermektir. Kaynak gösterirken bu sayfadaki hazır "
         "metni kullanabilirsiniz."),
        ("Veri ne sıklıkla güncelleniyor?",
         f"Son derleme {tarih}. Kaynak kurumların yayınları değiştikçe güncelleniyor. "
         "JSON dosyasındaki `cekim_tarihi` alanı derleme tarihini verir."),
        ("Veride ne var, ne yok?",
         f"Var: tesis adı, tür, bağlı kurum, il, ilçe, telefon ({telefonlu} kayıt), "
         f"e-posta, denize konum ({deniz} kayıt), yayımlanmış 2026 fiyatı "
         f"({fiyatli} kayıt), olanaklar ve kaynak bağlantısı. Yok: tam sokak adresi "
         "(çoğu tesis için yayımlanmamış), doluluk ve rezervasyon bilgisi. "
         "Tahmini hiçbir değer yoktur; bilinmeyen alan boş bırakılır."),
    ]

    icerik = f"""<div class="kap" style="max-width:820px;padding-block:34px 0">
<span class="rz rz-vurgu">{ik("kurum")}Açık veri</span>
<h1 style="margin:12px 0 10px">Veriyi kullanın, kaynak gösterin</h1>
<p class="ozet">Bu dizindeki {len(tesisler)} tesislik veri kümesi
<strong>CC BY 4.0</strong> ile açıktır. Araştırmada, haberde, kendi sitenizde
ya da bir uygulamada kullanabilirsiniz; tek koşul kaynak göstermeniz.
Veri kurumların kendi yayınlarından derlendi ve tahmini hiçbir değer içermiyor.</p>

<div class="yazi">
<h2>Dosyalar</h2>
<table><thead><tr><th>Dosya</th><th>İçerik</th></tr></thead><tbody>
<tr><td><a href="/tesisler.json">/tesisler.json</a></td>
<td>{len(tesisler)} tesisin tamamı: ad, tür, kurum, il, ilçe, telefon, e-posta,
denize konum, 2026 fiyatı, olanaklar, kaynak bağlantısı</td></tr>
<tr><td><a href="/data/tesis-tam.json">/data/tesis-tam.json</a></td>
<td>Koordinat, havuz ve fiyat alanı çıkarılmış hâliyle; araçların kullandığı biçim</td></tr>
<tr><td><a href="/data/harita.json">/data/harita.json</a></td>
<td>Harita noktaları: koordinat ve konum kesinliği</td></tr>
<tr><td><a href="/sitemap.xml">/sitemap.xml</a></td><td>{toplam_sayfa} sayfa</td></tr>
<tr><td><a href="/feed.xml">/feed.xml</a></td><td>RSS beslemesi</td></tr>
<tr><td><a href="/llms.txt">/llms.txt</a></td><td>Üretken arama motorları için özet</td></tr>
</tbody></table>
<p>Tüm JSON uçları <code>Access-Control-Allow-Origin: *</code> ile sunulur;
tarayıcıdan doğrudan çekebilirsiniz.</p>
</div>

<h2 style="margin-top:1.8em">Kaynak gösterme</h2>
<div class="alinti">
<h3>Metin olarak</h3>
<textarea readonly rows="2">{e(alinti_metin)}</textarea>
<p>Akademik ya da gazetecilik kullanımı için.</p>
</div>
<div class="alinti">
<h3>Sitenizde bağlantı olarak</h3>
<textarea readonly rows="3">{e(gomme)}</textarea>
<p>Bu HTML'i kopyalayıp sayfanıza yapıştırın.</p>
</div>

<div class="yazi" style="margin-top:1.8em">
<h2>Düzeltme ve katkı</h2>
<p>Yanlış telefon, kapanmış tesis ya da değişmiş fiyat gördüyseniz kaynağıyla
birlikte bildirin; düzeltilir. Bu dizin ticari değildir, reklam almaz ve
hiçbir kurumla ilişkisi yoktur.</p>
<h2>Sık sorulan sorular</h2>
</div>
{sss_html(sss)}
<div class="not" style="margin:24px 0 40px">{ik("bilgi")}<div>
Lisans yalnızca bu sitenin derlediği veri kümesi içindir. Fotoğraflar
Wikimedia Commons'a, kurum amblemleri ilgili kurumlara aittir; onların kendi
lisans koşulları geçerlidir.</div></div>
</div>"""

    return kabuk(
        baslik="Açık veri — 562 kamu tesisi, CC BY 4.0",
        aciklama=f"Türkiye'deki {len(tesisler)} kamu konaklama tesisinin açık veri "
        "kümesi. JSON olarak indirin, kaynak göstererek serbestçe kullanın.",
        yol="/veri/",
        icerik=icerik,
        kirintilar=kirintilar,
        jsonld=[sss_ld(sss), kirinti_ld(kirintilar)],
    )
