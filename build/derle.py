"""Siteyi derler: python build/derle.py"""

from __future__ import annotations

import json
import shutil
import sys
from collections import defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from genel import (  # noqa: E402
    BUGUN,
    REHBERLER,
    TARIH_TR,
    ana_sayfa,
    rehber_dizini,
    rehber_sayfasi,
    yaz,
)
from parca import AD, SITE, e, harita_kutusu, ik, il_karti, kabuk, tesis_karti  # noqa: E402
from uret import CIKTI, KOK, il_sayfasi, kirinti_ld, sss_html, sss_ld, tesis_sayfasi  # noqa: E402
from veri import TURLER, slug, tesis_slug, tur_slug  # noqa: E402


# --------------------------------------------------------------------------
def il_dizini(il_grup: dict, gorseller: dict) -> str:
    kirintilar = [("/", "Ana sayfa"), ("/il/", "İller")]
    toplam = sum(len(v) for v in il_grup.values())
    harfler = sorted({il[0] for il in il_grup})
    harf_iz = "".join(f'<a href="#h-{slug(h)}">{e(h)}</a>' for h in harfler)

    bloklar = ""
    for h in harfler:
        iller = sorted([i for i in il_grup if i[0] == h])
        kartlar = "".join(
            il_karti(i, len(il_grup[i]), sum(1 for t in il_grup[i] if t.get("deniz")), gorseller)
            for i in iller
        )
        bloklar += (
            f'<h2 id="h-{slug(h)}" style="margin:30px 0 14px">{e(h)}</h2>'
            f'<div class="iz-il">{kartlar}</div>'
        )

    icerik = f"""<section class="bl kap">
<div class="bl-bas"><div><h1>81 ilde kamu misafirhaneleri</h1>
<p>Türkiye'nin her ilindeki öğretmenevi, polisevi, üniversite ve bakanlık tesisleri —
toplam {toplam} kayıt. İl seçin, tesislerin telefon ve fiyat bilgilerine ulaşın.</p></div></div>
<ul class="harf-iz">{harf_iz}</ul>
{bloklar}</section>"""

    ld = {
        "@context": "https://schema.org",
        "@type": "ItemList",
        "name": "Türkiye'nin illerine göre kamu misafirhaneleri",
        "numberOfItems": len(il_grup),
        "itemListElement": [
            {"@type": "ListItem", "position": i, "name": il, "url": f"{SITE}/il/{slug(il)}/"}
            for i, il in enumerate(sorted(il_grup), 1)
        ],
    }
    return kabuk(
        baslik=f"81 İlde Kamu Misafirhaneleri — il il liste | {AD}",
        aciklama=f"Türkiye'nin 81 ilindeki {toplam} öğretmenevi, polisevi ve kamu "
        "misafirhanesi. İl seçerek telefon, fiyat ve yol tarifine ulaşın.",
        yol="/il/",
        icerik=icerik,
        kirintilar=kirintilar,
        aktif="/il/",
        jsonld=[ld, kirinti_ld(kirintilar)],
    )


def tur_sayfasi(tur: str, tesisler: list[dict], gorseller: dict) -> str:
    cogul, kisa, ikon, aciklama = TURLER[tur]
    yol = f"/tur/{tur_slug(tur)}/"
    kirintilar = [("/", "Ana sayfa"), (yol, cogul)]
    iller = sorted({t["il"] for t in tesisler})
    deniz = [t for t in tesisler if t.get("deniz")]
    fiyatli = [t for t in tesisler if t.get("fiyat_2026")]

    ozet = (
        f"Bu dizinde <strong>{len(tesisler)} {cogul.lower()}</strong> kayıtlı ve bunlar "
        f"<strong>{len(iller)} ile</strong> yayılmış durumda. {aciklama} "
        + (f"{len(deniz)} tesisin denize yakın konumu doğrulandı. " if deniz else "")
        + (f"{len(fiyatli)} tesisin yayımlanmış 2026 fiyatı sayfasında yer alıyor. " if fiyatli else "")
        + "Rezervasyon her tesisin kendi telefonundan yapılır."
    )

    sirali = sorted(tesisler, key=lambda t: (not t.get("deniz"), not t.get("fiyat_2026"), t["il"]))
    goster = sirali[:120]
    kalan = len(sirali) - len(goster)

    il_baglantilari = " · ".join(
        f'<a href="/il/{slug(i)}/">{e(i)}</a>' for i in iller
    )

    sss = [
        (f"Türkiye'de kaç {kisa.lower()} var?",
         f"Bu dizinde {len(tesisler)} {cogul.lower()} kayıtlı ve {len(iller)} ile "
         "dağılmış durumda. Liste kurumların kendi yayınlarından derlenmiştir."),
        (f"{cogul} kimlere açıktır?", aciklama),
    ]

    icerik = f"""<section class="bl kap">
<div class="bl-bas"><div>
<span class="rz rz-vurgu">{ik(ikon)}{e(kisa)}</span>
<h1 style="margin-top:10px">{e(cogul)}</h1></div></div>
<p class="ozet" style="max-width:78ch">{ozet}</p>
<div class="iz" style="margin-top:26px">
{"".join(tesis_karti(t, gorseller) for t in goster)}</div>
{f'<p style="color:var(--soluk);margin-top:22px">Listede ilk {len(goster)} tesis gösteriliyor. Kalan {kalan} tesise il sayfalarından ulaşabilirsiniz.</p>' if kalan > 0 else ""}
</section>
<section class="bl kap bl-cizgi">
<h2>İllere göre</h2>
<p style="color:var(--soluk);line-height:2.1">{il_baglantilari}</p>
</section>
<section class="bl kap bl-cizgi">
<h2>Sık sorulan sorular</h2>{sss_html(sss)}</section>"""

    return kabuk(
        baslik=f"{cogul} — {len(tesisler)} tesis, telefon ve fiyat | {AD}",
        aciklama=f"Türkiye'deki {len(tesisler)} {cogul.lower()}: telefon numaraları, "
        f"2026 fiyatları ve {len(iller)} ilde konum bilgisi.",
        yol=yol,
        icerik=icerik,
        kirintilar=kirintilar,
        aktif="/tur/ogretmenevleri/" if tur == "Öğretmenevi" else "",
        jsonld=[
            {
                "@context": "https://schema.org",
                "@type": "ItemList",
                "name": cogul,
                "numberOfItems": len(tesisler),
                "itemListElement": [
                    {"@type": "ListItem", "position": i,
                     "url": f"{SITE}/tesis/{tesis_slug(t)}/", "name": t["ad"]}
                    for i, t in enumerate(sirali, 1)
                ],
            },
            sss_ld(sss),
            kirinti_ld(kirintilar),
        ],
    )


def deniz_sayfasi(tesisler: list[dict], gorseller: dict) -> str:
    deniz = sorted(
        [t for t in tesisler if t.get("deniz")],
        key=lambda t: (t.get("ankara_saat") or 99, t["il"]),
    )
    iller = sorted({t["il"] for t in deniz})
    kirintilar = [("/", "Ana sayfa"), ("/deniz/", "Denize yakın tesisler")]
    havuzlu = sum(1 for t in deniz if any("havuz" in o.lower() for o in t.get("olanaklar") or []))

    ozet = (
        f"Denize konumu tesisin kendi yayınından doğrulanmış <strong>{len(deniz)} kamu "
        f"tesisi</strong> var; bunlar {len(iller)} kıyı iline dağılmış durumda. "
        f"{havuzlu} tesiste havuz kayıtlı. Liste, Ankara'ya en yakın olandan başlayarak "
        "sıralanmıştır. Bir ilin kıyıda olması tesisin denize yakın olduğu anlamına "
        "gelmez; bu sayfada yalnızca konumu açıkça belirtilmiş tesisler yer alır."
    )

    sss = [
        ("Denize sıfır kamu misafirhanesi var mı?",
         f"Bu dizinde denize yakın konumu doğrulanmış {len(deniz)} tesis bulunuyor. "
         "Bir kısmı doğrudan sahil şeridinde, bir kısmı denize yürüme mesafesinde."),
        ("Hangi illerde denize yakın kamu tesisi var?",
         "Doğrulanmış tesislerin bulunduğu iller: " + ", ".join(iller) + "."),
    ]

    icerik = f"""<section class="bl kap">
<div class="bl-bas"><div>
<span class="rz rz-deniz">{ik("deniz")}Deniz</span>
<h1 style="margin-top:10px">Denize yakın kamu tesisleri</h1></div>
<a class="dg dg-2 dg-sm" href="/rehber/ankaraya-yakin-deniz-tatili/">
Ankara'ya yakın olanlar{ik("ok")}</a></div>
<p class="ozet" style="max-width:78ch">{ozet}</p>
<div class="iz" style="margin-top:26px">
{"".join(tesis_karti(t, gorseller) for t in deniz)}</div>
</section>
<section class="bl kap bl-cizgi"><h2>Sık sorulan sorular</h2>{sss_html(sss)}</section>"""

    return kabuk(
        baslik=f"Denize Yakın Kamu Misafirhaneleri — {len(deniz)} tesis | {AD}",
        aciklama=f"Denize konumu doğrulanmış {len(deniz)} öğretmenevi, polisevi ve kamu "
        f"tesisi. {len(iller)} kıyı ilinde, Ankara'ya uzaklığa göre sıralı.",
        yol="/deniz/",
        icerik=icerik,
        kirintilar=kirintilar,
        aktif="/deniz/",
        jsonld=[
            {
                "@context": "https://schema.org",
                "@type": "ItemList",
                "name": "Denize yakın kamu konaklama tesisleri",
                "numberOfItems": len(deniz),
                "itemListElement": [
                    {"@type": "ListItem", "position": i,
                     "url": f"{SITE}/tesis/{tesis_slug(t)}/", "name": t["ad"]}
                    for i, t in enumerate(deniz, 1)
                ],
            },
            sss_ld(sss),
            kirinti_ld(kirintilar),
        ],
    )


def kaynaklar_sayfasi(tesisler: list[dict], gorseller: dict, kurumlar: dict) -> str:
    kirintilar = [("/", "Ana sayfa"), ("/kaynaklar/", "Kaynaklar")]
    logolar = "".join(
        f'<a class="logo-h" href="{e(v["site"])}" target="_blank" rel="noopener nofollow" '
        f'title="{e(v["ad"])}"><img src="/img/kurum/{v["dosya"]}" width="256" height="256" '
        f'loading="lazy" decoding="async" alt="{e(v["ad"])} amblemi"></a>'
        for v in kurumlar.values()
        if v.get("dosya")
    )
    foto_satir = "".join(
        f'<tr><td><a href="/il/{slug(il)}/">{e(il)}</a></td><td>{e(g["yazar"])[:70]}</td>'
        f'<td>{e(g["lisans"])}</td>'
        f'<td><a href="{e(g["sayfa"])}" target="_blank" rel="noopener nofollow">dosya</a></td></tr>'
        for il, g in sorted(gorseller.items())
    )
    icerik = f"""<div class="kap" style="max-width:860px;padding-block:34px 0">
<h1>Kaynaklar ve katkı</h1>
<div class="yazi">
<p>Bu dizindeki {len(tesisler)} kaydın tamamı kurumların kendi yayınlarından derlendi.
<strong>Hiçbir telefon, e-posta veya fiyat tahminle yazılmadı;</strong> bulunamayan alan
boş bırakıldı. Son derleme: {TARIH_TR}.</p>

<h2>Veri kaynağı kurumlar</h2>
<p>Aşağıdaki amblemler ilgili kurumlara aittir ve yalnızca verinin hangi kurumdan
geldiğini göstermek ve o kuruma bağlantı vermek için kullanılmaktadır. Bu site
hiçbir kurumla ilişkili değildir.</p>
</div>
<div class="logo-duvar" style="margin:20px 0 34px">{logolar}</div>
<div class="yazi">
<h2>Alan bazında kaynak</h2>
<table><thead><tr><th>Alan</th><th>Kaynak</th></tr></thead><tbody>
<tr><td>Öğretmenevi adı, il, ilçe, telefon</td>
<td><a href="https://dhgm.meb.gov.tr/edestek/ogretmenevi/ogretmenevi_liste.aspx"
target="_blank" rel="noopener nofollow">MEB Destek Hizmetleri öğretmenevi listesi</a></td></tr>
<tr><td>Polisevi, bakanlık ve üniversite tesisleri</td>
<td>Kurumun kendi .gov.tr / .edu.tr sayfası — her tesis sayfasında kaynak bağlantısı var</td></tr>
<tr><td>2026 fiyatları</td><td>Tesisin kendi yayımladığı fiyat listesi</td></tr>
<tr><td>Ankara mesafesi</td><td>Bilinen karayolu mesafelerinden yaklaşık hesap, ölçülmüş değil</td></tr>
<tr><td>İl fotoğrafları</td><td>Wikimedia Commons, serbest lisanslı — tablo aşağıda</td></tr>
</tbody></table>

<h2>Fotoğraflar hakkında</h2>
<p>Tesislerin kendi fotoğrafları elimizde yok. Olmayan fotoğrafı stok görselle
doldurmak yerine <strong>her ilin kendi fotoğrafını</strong> kullanıyoruz; fotoğraflar
tesisin değil, ilin görüntüsüdür ve sayfada böyle etiketlenmiştir. Tamamı Wikimedia
Commons'tan serbest lisanslarla alınmıştır.</p>
<table><thead><tr><th>İl</th><th>Fotoğrafçı</th><th>Lisans</th><th>Kaynak</th></tr></thead>
<tbody>{foto_satir}</tbody></table>

<h2>Düzeltme bildirin</h2>
<p>Yanlış bir telefon, kapanmış bir tesis veya değişmiş bir fiyat gördüyseniz
bildirin — kaynağıyla birlikte düzeltilir. Bu dizin ticari değildir, reklam almaz.</p>
</div>
<div class="not" style="margin:24px 0 40px">{ik("uyari")}<div>
<strong>Bağımsız dizindir.</strong> Hiçbir kuruma ait değildir, hiçbir kurumu temsil
etmez ve rezervasyon almaz. Bağlayıcı bilgi için tesisin bağlı olduğu kuruma başvurun.</div></div>
</div>"""
    return kabuk(
        baslik=f"Kaynaklar ve Katkı | {AD}",
        aciklama="Bu dizindeki verilerin hangi kurumlardan derlendiği, fotoğraf "
        "lisansları ve düzeltme bildirimi.",
        yol="/kaynaklar/",
        icerik=icerik,
        kirintilar=kirintilar,
        jsonld=[kirinti_ld(kirintilar)],
    )




def harita_sayfasi(tesisler: list[dict], konumlar: dict) -> str:
    kirintilar = [("/", "Ana sayfa"), ("/harita/", "Harita")]
    var = [t for t in tesisler if konumlar.get(tesis_slug(t))]
    kesin = sum(1 for t in var if konumlar[tesis_slug(t)]["kesinlik"] == "tesis")
    iller = len({t["il"] for t in var})

    ozet = (
        f"Haritada <strong>{len(var)} tesis</strong> işaretli. Bunlardan "
        f"<strong>{kesin} tanesinin</strong> konumu OpenStreetMap kaydından birebir "
        f"alındı; kalan {len(var) - kesin} tesis için ilçe merkezi gösteriliyor ve "
        "işaret kesikli çizgiyle bunu belli eder. Hiçbir konum tahminle "
        f"işaretlenmedi. Tesisler {iller} ile yayılmış durumda."
    )
    sss = [
        ("Haritadaki konumlar tam adres mi?",
         f"{kesin} tesisin konumu OpenStreetMap kaydından alınmıştır ve tesisin "
         "kendisini gösterir. Diğer tesisler için ilçe merkezi işaretlenir; bu "
         "yaklaşık bir konumdur ve haritada kesikli iğneyle gösterilir. Tam adres "
         "için tesisin telefonundan bilgi alınmalıdır."),
        ("Haritada tesis nasıl bulunur?",
         "Haritayı yakınlaştırdıkça kümeler açılır ve tek tek tesisler görünür. "
         "Bir iğneye tıklayınca tesis adı ve sayfasına bağlantı çıkar."),
    ]

    icerik = f"""<section class="bl kap harita-tam">
<div class="bl-bas"><div>
<span class="rz rz-vurgu">{ik("harita")}Harita</span>
<h1 style="margin-top:10px">Kamu misafirhaneleri haritası</h1></div>
<a class="dg dg-2 dg-sm" href="/il/">İl listesi{ik("ok")}</a></div>
<p class="ozet" style="max-width:78ch;margin-bottom:22px">{ozet}</p>
{harita_kutusu(ozellikler='data-tum="1"', say_kimlik=True)}
</section>
<section class="bl kap bl-cizgi"><h2>Sık sorulan sorular</h2>{sss_html(sss)}</section>"""

    return kabuk(
        baslik=f"Kamu Misafirhaneleri Haritası — {len(var)} tesis | {AD}",
        aciklama=f"Türkiye'deki {len(var)} öğretmenevi, polisevi ve kamu misafirhanesinin "
        "haritası. Tesise tıklayarak telefon, fiyat ve yol tarifine ulaşın.",
        yol="/harita/",
        icerik=icerik,
        kirintilar=kirintilar,
        aktif="/harita/",
        harita=True,
        jsonld=[sss_ld(sss), kirinti_ld(kirintilar)],
    )


def ara_sayfasi(tesisler: list[dict]) -> str:
    kirintilar = [("/", "Ana sayfa"), ("/ara/", "Ara")]
    icerik = f"""<section class="bl kap" style="max-width:760px">
<h1>Tesis ara</h1>
<p style="color:var(--soluk)">{len(tesisler)} tesis içinde ada, ilçeye veya ile göre arayın.</p>
<div class="ara" style="max-width:100%">
<svg class="ik ik-ara" viewBox="0 0 24 24" aria-hidden="true"><path d="M17.5 17.5 21 21M19.5 11.2a8.2 8.2 0 1 1-16.5 0 8.2 8.2 0 0 1 16.5 0Z"/></svg>
<input type="search" id="q" placeholder="Örn. Ayvalık, Sinop Öğretmenevi, Muğla" autocomplete="off"
role="combobox" aria-expanded="false" aria-controls="oneri" aria-label="Tesis ara" autofocus>
<div class="oneri" id="oneri" role="listbox"></div>
</div>
<p id="sonuc-say" style="color:var(--soluk);font-size:.88rem;margin:16px 0 0"></p>
<div id="sonuclar"></div>
</section>"""
    return kabuk(
        baslik=f"Tesis ara | {AD}",
        aciklama=f"{len(tesisler)} kamu konaklama tesisi içinde ada, ilçeye veya ile göre arama.",
        yol="/ara/",
        icerik=icerik,
        kirintilar=kirintilar,
        jsonld=[kirinti_ld(kirintilar)],
    )


def dortyuzdort() -> str:
    return kabuk(
        baslik=f"Sayfa bulunamadı | {AD}",
        aciklama="Aradığınız sayfa bulunamadı.",
        yol="/404.html",
        icerik=f"""<div class="bos" style="padding:90px 20px">{ik("bos")}
<h1 style="margin-bottom:10px">Sayfa bulunamadı</h1>
<p>Aradığınız tesis taşınmış veya adres yanlış olabilir.</p>
<div style="display:flex;gap:10px;justify-content:center;margin-top:20px;flex-wrap:wrap">
<a class="dg dg-1" href="/">Ana sayfa</a>
<a class="dg dg-2" href="/il/">81 il listesi</a></div></div>""",
    )


# --------------------------------------------------------------------------
def sitemap(yollar: list[str]) -> str:
    ogeler = "".join(
        f"<url><loc>{SITE}{y}</loc><lastmod>{BUGUN.isoformat()}</lastmod>"
        f"<changefreq>{'weekly' if y.count('/') < 3 else 'monthly'}</changefreq>"
        f"<priority>{'1.0' if y == '/' else '0.8' if y.count('/') < 3 else '0.6'}</priority></url>"
        for y in yollar
    )
    return (
        '<?xml version="1.0" encoding="UTF-8"?>'
        '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">'
        f"{ogeler}</urlset>"
    )


def llms_txt(tesisler: list[dict], il_grup: dict) -> str:
    deniz = [t for t in tesisler if t.get("deniz")]
    fiyatli = [t for t in tesisler if t.get("fiyat_2026")]
    return f"""# {AD}

> Türkiye'nin 81 ilindeki {len(tesisler)} kamu konaklama tesisinin (öğretmenevi,
> polisevi, üniversite misafirhanesi, bakanlık tesisi) bağımsız dizini.
> Bilgiler kurumların kendi yayınlarından derlenmiştir; tahmini veri yoktur.

Son güncelleme: {TARIH_TR}

## Veri kümesi
- Toplam tesis: {len(tesisler)}
- Öğretmenevi: {sum(1 for t in tesisler if t["tur"] == "Öğretmenevi")}
- Polisevi: {sum(1 for t in tesisler if t["tur"] == "Polisevi")}
- Üniversite misafirhanesi: {sum(1 for t in tesisler if t["tur"] == "Üniversite Misafirhanesi")}
- Kamu misafirhanesi: {sum(1 for t in tesisler if t["tur"] == "Kamu Misafirhanesi")}
- Telefon numarası doğrulanmış: {sum(1 for t in tesisler if t.get("telefon"))}
- Denize yakın konumu doğrulanmış: {len(deniz)}
- Yayımlanmış 2026 fiyatı bulunan: {len(fiyatli)}
- İl sayısı: {len(il_grup)}

## Ham veri
- [Tüm tesisler (JSON)]({SITE}/tesisler.json): tesis adı, tür, kurum, il, ilçe,
  telefon listesi, e-posta, denize konumu, 2026 fiyatı, olanaklar, kaynak bağlantısı.
- [Arama dizini (JSON)]({SITE}/data/ara.json)

## Rehber sayfaları
""" + "".join(
        f"- [{b}]({SITE}/rehber/{s}/)\n" for s, b, _ in REHBERLER
    ) + f"""
## Önemli notlar
- Bu site rezervasyon almaz. Rezervasyon her tesisin kendi telefonundan yapılır;
  merkezî bir rezervasyon sistemi yoktur.
- Fiyat yalnızca tesisin kendisi yayımlamışsa yazılır; tahmini fiyat verilmez.
- Ankara mesafeleri yaklaşık karayolu değerleridir, ölçülmemiştir.
- Site hiçbir kuruma ait değildir ve hiçbir kurumu temsil etmez.
"""


def robots() -> str:
    return f"""User-agent: *
Allow: /

Sitemap: {SITE}/sitemap.xml
"""


# --------------------------------------------------------------------------
def main() -> int:
    veri = json.loads((KOK / "tesisler.json").read_text("utf-8"))
    tesisler = veri["tesisler"]
    gorseller = json.loads((KOK / "data" / "gorseller.json").read_text("utf-8"))
    kurumlar = json.loads((KOK / "data" / "kurumlar.json").read_text("utf-8"))
    kyol = KOK / "data" / "konumlar.json"
    konumlar = (
        {k: v for k, v in json.loads(kyol.read_text("utf-8")).items() if v}
        if kyol.exists()
        else {}
    )

    if CIKTI.exists():
        shutil.rmtree(CIKTI)
    CIKTI.mkdir(parents=True)

    il_grup: dict[str, list[dict]] = defaultdict(list)
    for t in tesisler:
        il_grup[t["il"]].append(t)

    yollar = ["/", "/il/", "/deniz/", "/rehber/", "/kaynaklar/", "/ara/"]
    if konumlar:
        yollar.append("/harita/")
    else:
        # koordinat yoksa harita sayfası üretilmez; menüde de yer almasın
        import parca

        parca.GEZ = [g for g in parca.GEZ if g[0] != "/harita/"]

    yaz("/", ana_sayfa(tesisler, gorseller, kurumlar))
    yaz("/il/", il_dizini(il_grup, gorseller))
    yaz("/deniz/", deniz_sayfasi(tesisler, gorseller))
    yaz("/kaynaklar/", kaynaklar_sayfasi(tesisler, gorseller, kurumlar))
    yaz("/rehber/", rehber_dizini(tesisler))
    yaz("/ara/", ara_sayfasi(tesisler))
    if konumlar:
        yaz("/harita/", harita_sayfasi(tesisler, konumlar))
    (CIKTI / "404.html").write_text(dortyuzdort(), "utf-8")

    for anahtar, baslik, ikon in REHBERLER:
        yaz(f"/rehber/{anahtar}/", rehber_sayfasi(anahtar, baslik, ikon, tesisler))
        yollar.append(f"/rehber/{anahtar}/")

    for il, ts in il_grup.items():
        il_haritali = any(konumlar.get(tesis_slug(t)) for t in ts)
        yaz(f"/il/{slug(il)}/", il_sayfasi(il, ts, gorseller, il_haritali))
        yollar.append(f"/il/{slug(il)}/")

    for tur in TURLER:
        alt = [t for t in tesisler if t["tur"] == tur]
        if alt:
            yaz(f"/tur/{tur_slug(tur)}/", tur_sayfasi(tur, alt, gorseller))
            yollar.append(f"/tur/{tur_slug(tur)}/")

    for t in tesisler:
        komsular = [k for k in il_grup[t["il"]] if k is not t][:3]
        yaz(f"/tesis/{tesis_slug(t)}/",
            tesis_sayfasi(t, gorseller, komsular, konumlar.get(tesis_slug(t))))
        yollar.append(f"/tesis/{tesis_slug(t)}/")

    # arama dizini — [ad, ilce, il, slug, tur kisaltmasi]
    tur_kod = {k: i for i, k in enumerate(TURLER)}
    dizin = [
        [t["ad"], t["ilce"], t["il"], tesis_slug(t), tur_kod[t["tur"]],
         1 if t.get("deniz") else 0]
        for t in tesisler
    ]
    (CIKTI / "data").mkdir(exist_ok=True)
    (CIKTI / "data" / "ara.json").write_text(
        json.dumps({"turler": list(TURLER), "t": dizin}, ensure_ascii=False,
                   separators=(",", ":")), "utf-8"
    )

    if konumlar:
        tur_kod2 = {k: i for i, k in enumerate(TURLER)}
        hnoktalar = []
        for t in tesisler:
            k = konumlar.get(tesis_slug(t))
            if not k:
                continue
            hnoktalar.append([k["lat"], k["lon"], t["ad"], tesis_slug(t), t["il"],
                              t["ilce"], tur_kod2[t["tur"]], 1 if t.get("deniz") else 0,
                              1 if k["kesinlik"] == "tesis" else 0])
        (CIKTI / "data" / "harita.json").write_text(
            json.dumps({"turler": list(TURLER), "t": hnoktalar}, ensure_ascii=False,
                       separators=(",", ":")), "utf-8")

    (CIKTI / "sitemap.xml").write_text(sitemap(yollar), "utf-8")
    (CIKTI / "robots.txt").write_text(robots(), "utf-8")
    (CIKTI / "llms.txt").write_text(llms_txt(tesisler, il_grup), "utf-8")
    shutil.copy(KOK / "tesisler.json", CIKTI / "tesisler.json")
    shutil.copy(KOK / "favicon.svg", CIKTI / "favicon.svg")
    shutil.copytree(KOK / "static", CIKTI / "static")
    shutil.copytree(KOK / "img", CIKTI / "img")

    boyut = sum(f.stat().st_size for f in CIKTI.rglob("*") if f.is_file())
    print(f"{len(yollar)} sayfa · {len(list(CIKTI.rglob('*.html')))} html "
          f"· {boyut / 1024 / 1024:.1f} MB -> {CIKTI}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
