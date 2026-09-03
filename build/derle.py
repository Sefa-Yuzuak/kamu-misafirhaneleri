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
from araclar import (  # noqa: E402
    ARACLAR,
    araclar_dizini,
    butce_sayfasi,
    en_yakin_sayfasi,
    karsilastir_sayfasi,
    mesafe_sayfasi,
)
from blog import (  # noqa: E402
    ETIKET,
    etiket_dizini,
    etiket_sayfasi,
    gezi_dizini,
    il_gezi_sayfasi,
    ilce_sayfasi,
    temiz_yerler,
)
from dagitim import (  # noqa: E402
    INDEXNOW_ANAHTAR,
    manifest,
    opensearch,
    rss,
    veri_sayfasi,
)
from listeler import liste_sayfasi, liste_tanimlari, listeler_dizini  # noqa: E402
from mesafe import en_yakinlar, il_merkezleri  # noqa: E402
import yazitipi  # noqa: E402
from stil import yayimla  # noqa: E402
from parca import AD, SITE, e, harita_kutusu, ik, il_karti, kabuk, tesis_karti  # noqa: E402
from rota import (  # noqa: E402
    duraklar as rota_duraklari,
    rota_dizini,
    rota_sayfasi,
    rota_slug,
    rotalar_uret,
    veriyi_yukle as rota_verisi,
)
from uret import CIKTI, KOK, il_sayfasi, kirinti_ld, sss_html, sss_ld, tesis_sayfasi  # noqa: E402
from veri import TURLER, fiyat_taban, kisa_ad, slug, tesis_slug, tur_slug  # noqa: E402


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
        baslik="81 İlde Kamu Misafirhaneleri — il il tam liste",
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
    kirintilar = [("/", "Ana sayfa"), ("/tur/", "Tesis türleri"), (yol, cogul)]
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
<h2 class="gizli">{e(cogul)} listesi</h2>
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
        baslik=f"{cogul} — {len(tesisler)} tesis, telefon ve fiyat",
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


def tur_dizini(tesisler: list[dict]) -> str:
    """/tur/ kök sayfası: tesis türlerinin dizini.

    Tür sayfaları üretiliyordu ama kök adres boştu ve canlıda 403 dönüyordu.
    """
    kirintilar = [("/", "Ana sayfa"), ("/tur/", "Tesis türleri")]
    gruplar = [(tur, [t for t in tesisler if t["tur"] == tur]) for tur in TURLER]
    gruplar = [(tur, alt) for tur, alt in gruplar if alt]

    kartlar = ""
    for tur, alt in gruplar:
        cogul, kisa, ikon, aciklama = TURLER[tur]
        iller = len({t["il"] for t in alt})
        deniz = sum(1 for t in alt if t.get("deniz"))
        kartlar += (
            f'<a class="tur-k" href="/tur/{tur_slug(tur)}/">{ik(ikon, "ik tur-ik")}'
            f'<strong>{e(cogul)}</strong>'
            f'<em>{len(alt)} tesis · {iller} il'
            + (f" · {deniz} deniz kıyısı" if deniz else "")
            + f'</em><span class="tur-ok">{ik("ok")}</span></a>'
        )

    satirlar = "".join(
        f"<tr><td><a href=\"/tur/{tur_slug(tur)}/\">{e(TURLER[tur][0])}</a></td>"
        f"<td>{len(alt)}</td>"
        f"<td>{len({t['il'] for t in alt})}</td>"
        f"<td>{sum(1 for t in alt if t.get('fiyat_2026'))}</td></tr>"
        for tur, alt in gruplar
    )

    sss = [
        ("Kamu misafirhaneleri kaç türe ayrılır?",
         "Bu dizinde " + ", ".join(TURLER[t][0].lower() for t, _ in gruplar)
         + f" olmak üzere {len(gruplar)} tür bulunuyor; toplam {len(tesisler)} tesis "
         "kayıtlıdır."),
        ("Hangi türde konaklayabilirim?",
         "Her tür kendi kurumunun personeline ve birinci derece yakınlarına önceliklidir; "
         "boş kapasite durumunda diğer kamu personeli ve kimi tesislerde herkes "
         "konaklayabilir. Kesin bilgi için tesisin telefonundan teyit alın."),
    ]

    icerik = f"""<section class="bl kap">
<div class="bl-bas"><div><h1>Tesis türleri</h1>
<p>Türkiye'deki <strong>{len(tesisler)} kamu konaklama tesisi</strong> bağlı olduğu
kuruma göre {len(gruplar)} türe ayrılıyor. Tür seçin, o türdeki tesisleri telefon
ve fiyat bilgileriyle görün.</p></div></div>
<div class="tur-iz" style="margin-top:24px">{kartlar}</div>
</section>
<section class="bl kap bl-cizgi">
<h2>Türlere göre sayılar</h2>
<div class="yazi"><table>
<thead><tr><th>Tür</th><th>Tesis</th><th>İl</th><th>Fiyatı yayımlanan</th></tr></thead>
<tbody>{satirlar}</tbody></table></div>
</section>
<section class="bl kap bl-cizgi">
<h2>Sık sorulan sorular</h2>{sss_html(sss)}</section>"""

    ld = {
        "@context": "https://schema.org",
        "@type": "ItemList",
        "name": "Kamu konaklama tesisi türleri",
        "numberOfItems": len(gruplar),
        "itemListElement": [
            {"@type": "ListItem", "position": i, "name": TURLER[tur][0],
             "url": f"{SITE}/tur/{tur_slug(tur)}/"}
            for i, (tur, _) in enumerate(gruplar, 1)
        ],
    }
    return kabuk(
        baslik=f"Tesis Türleri — {len(tesisler)} kamu misafirhanesi {len(gruplar)} türde",
        aciklama=f"Öğretmenevi, polisevi, üniversite ve kamu misafirhanesi: "
        f"{len(tesisler)} tesis türlerine göre ayrılmış, telefon ve fiyatlarıyla.",
        yol="/tur/",
        icerik=icerik,
        kirintilar=kirintilar,
        jsonld=[ld, sss_ld(sss), kirinti_ld(kirintilar)],
    )


def tesis_dizini(tesisler: list[dict], il_grup: dict) -> str:
    """/tesis/ kök sayfası: bütün tesislerin il il tam dizini.

    562 tesis sayfası bu kökün altında duruyordu ama kökün kendisi boştu ve
    canlıda 403 dönüyordu. Tam dizin aynı zamanda her tesis sayfasına doğrudan
    bir iç bağlantı verir.
    """
    kirintilar = [("/", "Ana sayfa"), ("/tesis/", "Tüm tesisler")]
    iller = sorted(il_grup)
    harfler = sorted({i[0] for i in iller})
    harf_iz = "".join(f'<a href="#h-{slug(h)}">{e(h)}</a>' for h in harfler)

    bloklar = ""
    for h in harfler:
        bloklar += f'<h2 id="h-{slug(h)}" style="margin:30px 0 12px">{e(h)}</h2>'
        for il in [i for i in iller if i[0] == h]:
            alt = sorted(il_grup[il], key=lambda t: kisa_ad(t["ad"]))
            baglar = " · ".join(
                f'<a href="/tesis/{tesis_slug(t)}/">{e(kisa_ad(t["ad"]))}</a>'
                for t in alt
            )
            bloklar += (
                f'<h3 style="margin:18px 0 6px"><a href="/il/{slug(il)}/">{e(il)}</a> '
                f'<span style="color:var(--soluk);font-weight:400">({len(alt)})</span></h3>'
                f'<p style="color:var(--soluk);line-height:2.1">{baglar}</p>'
            )

    fiyatli = sum(1 for t in tesisler if t.get("fiyat_2026"))
    icerik = f"""<section class="bl kap">
<div class="bl-bas"><div><h1>Tüm tesisler</h1>
<p>Dizindeki <strong>{len(tesisler)} kamu konaklama tesisinin</strong> tamamı,
{len(iller)} ile göre sıralanmış hâlde. {fiyatli} tesisin yayımlanmış 2026 fiyatı
sayfasında yer alıyor. Tesis adına tıklayarak telefon, adres ve yol tarifine
ulaşabilirsiniz.</p></div></div>
<ul class="harf-iz">{harf_iz}</ul>
{bloklar}</section>"""

    ld = {
        "@context": "https://schema.org",
        "@type": "ItemList",
        "name": "Türkiye'deki kamu konaklama tesislerinin tam listesi",
        "numberOfItems": len(tesisler),
        "itemListElement": [
            {"@type": "ListItem", "position": i, "name": t["ad"],
             "url": f"{SITE}/tesis/{tesis_slug(t)}/"}
            for i, t in enumerate(
                sorted(tesisler, key=lambda t: (t["il"], kisa_ad(t["ad"]))), 1
            )
        ],
    }
    return kabuk(
        baslik=f"Tüm Tesisler — {len(tesisler)} kamu misafirhanesi tam liste",
        aciklama=f"Türkiye'deki {len(tesisler)} öğretmenevi, polisevi ve kamu "
        f"misafirhanesinin il il tam listesi; telefon, fiyat ve konum bilgileriyle.",
        yol="/tesis/",
        icerik=icerik,
        kirintilar=kirintilar,
        jsonld=[ld, kirinti_ld(kirintilar)],
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
<h2 class="gizli">Denize yakın tesislerin listesi</h2>
<div class="iz" style="margin-top:26px">
{"".join(tesis_karti(t, gorseller) for t in deniz)}</div>
</section>
<section class="bl kap bl-cizgi"><h2>Sık sorulan sorular</h2>{sss_html(sss)}</section>"""

    return kabuk(
        baslik=f"Denize Yakın Kamu Misafirhaneleri — {len(deniz)} tesis",
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
        baslik="Kaynaklar, veri kaynağı kurumlar ve fotoğraf lisansları",
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
        baslik=f"Kamu Misafirhaneleri Haritası — {len(var)} tesis",
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
        baslik="Tesis ara — 562 kamu misafirhanesi içinde arama",
        aciklama=f"{len(tesisler)} kamu konaklama tesisi içinde ada, ilçeye veya ile göre arama.",
        yol="/ara/",
        icerik=icerik,
        kirintilar=kirintilar,
        jsonld=[kirinti_ld(kirintilar)],
    )


def dortyuzdort() -> str:
    return kabuk(
        baslik="Sayfa bulunamadı — Kamu Misafirhaneleri",
        aciklama="Aradığınız sayfa bulunamadı. 81 ildeki 562 kamu konaklama tesisine ana sayfadan veya il listesinden ulaşabilirsiniz.",
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
    # 81 il sayfasi tek tek listeleniyor: llms.txt yalnizca 5 rehber
    # sayfasini gosterdigi icin AI motorlari sitenin govdesini bulamiyordu.
    il_satirlari = "\n".join(
        f"- [{il} ({len(ts)} tesis)]({SITE}/il/{slug(il)}/)"
        for il, ts in sorted(il_grup.items())
    )
    return f"""# {AD}

> Türkiye'nin 81 ilindeki {len(tesisler)} kamu konaklama tesisinin (öğretmenevi,
> polisevi, üniversite misafirhanesi, bakanlık tesisi) bağımsız dizini.
> Bilgiler kurumların kendi yayınlarından derlenmiştir; tahmini veri yoktur.

Son güncelleme: {TARIH_TR}

## Site haritası
- Bütün adresler: {SITE}/sitemap.xml ({len(tesisler)} tesis sayfası dahil)
- Düz metin adres listesi: {SITE}/urls.txt
- Tüm tesisler (il il): {SITE}/tesis/
- Tesis türleri: {SITE}/tur/
- İl dizini: {SITE}/il/
- Gezi rehberi: {SITE}/gezi/  ·  Konu başlıkları: {SITE}/etiket/
- Çok duraklı rotalar (harita, gezi, yöresel yemek, maliyet): {SITE}/rota/
- Sıralı listeler: {SITE}/liste/  ·  Hesaplama araçları: {SITE}/araclar/
- Harita: {SITE}/harita/  ·  Açık veri: {SITE}/veri/

## İl sayfaları
{il_satirlari}

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
- Mesafeler koordinatlardan (OpenStreetMap Nominatim) hesaplanan tahminlerdir:
  kuş uçuşu uzaklık × 1,27. Bilinen güzergâhlarda sapma ortalama %6'dır.
  Ölçülmüş karayolu mesafesi değildir.
- 161 tesisin konumu OSM kaydından birebir alındı; kalan 400 tesiste ilçe merkezi
  kullanılır ve bu `kesinlik` alanıyla işaretlidir.
- Site hiçbir kuruma ait değildir ve hiçbir kurumu temsil etmez.
"""


def robots() -> str:
    """Tüm tarayıcılara açık. Üretken arama motorlarının tarayıcıları da
    açıkça karşılanıyor: alıntılanmak istiyoruz, engellemek işimize gelmez."""
    return f"""User-agent: *
Allow: /

# Üretken arama motorları — içeriğin alıntılanmasını istiyoruz
User-agent: GPTBot
Allow: /
User-agent: OAI-SearchBot
Allow: /
User-agent: ClaudeBot
Allow: /
User-agent: PerplexityBot
Allow: /
User-agent: Google-Extended
Allow: /
User-agent: Applebot-Extended
Allow: /
User-agent: CCBot
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

    # Klasörün kendisi silinmez: yerel bir sunucu onu açık tutuyor olabilir.
    CIKTI.mkdir(parents=True, exist_ok=True)
    for cocuk in CIKTI.iterdir():
        shutil.rmtree(cocuk) if cocuk.is_dir() else cocuk.unlink()

    import parca

    parca.STIL_YOLU = yayimla(CIKTI)

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
        il_merkez = il_merkezleri(konumlar)
        yaz("/araclar/", araclar_dizini(tesisler, konumlar))
        yollar.append("/araclar/")
        for anahtar, uretici in (
            ("en-yakin", en_yakin_sayfasi),
            ("tatil-butcesi", butce_sayfasi),
            ("mesafe", mesafe_sayfasi),
        ):
            yaz(f"/araclar/{anahtar}/", uretici(tesisler, konumlar, il_merkez))
            yollar.append(f"/araclar/{anahtar}/")
        yaz("/araclar/karsilastir/", karsilastir_sayfasi(tesisler))
        yollar.append("/araclar/karsilastir/")

        tanimlar = liste_tanimlari(konumlar)
        yaz("/liste/", listeler_dizini(tanimlar, tesisler, konumlar))
        yollar.append("/liste/")
        for anahtar, tanim in tanimlar.items():
            sayfa = liste_sayfasi(anahtar, tanim, tesisler, konumlar)
            if sayfa:
                yaz(f"/liste/{anahtar}/", sayfa)
                yollar.append(f"/liste/{anahtar}/")
    else:
        import parca

        parca.GEZ = [g for g in parca.GEZ if g[0] not in ("/araclar/", "/liste/")]
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

    # Rotalar: koordinati dogrulanmis tesisleri gunluk surus mesafesinde
    # zincirleyip cok duraklı gezi programlari uretir.
    _gezi_v, _mutfak_v = rota_verisi()
    _rotalar = rotalar_uret(rota_duraklari(tesisler, konumlar, _gezi_v))
    if _rotalar:
        yaz("/rota/", rota_dizini(_rotalar))
        yollar.append("/rota/")
        for _r in _rotalar:
            yaz(f"/rota/{rota_slug(_r)}/", rota_sayfasi(_r, _mutfak_v, gorseller))
            yollar.append(f"/rota/{rota_slug(_r)}/")
        print(f"rota: {len(_rotalar)} rota, {sum(len(r) for r in _rotalar)} durak")

    yaz("/tur/", tur_dizini(tesisler))
    yollar.append("/tur/")
    yaz("/tesis/", tesis_dizini(tesisler, il_grup))
    yollar.append("/tesis/")

    for tur in TURLER:
        alt = [t for t in tesisler if t["tur"] == tur]
        if alt:
            yaz(f"/tur/{tur_slug(tur)}/", tur_sayfasi(tur, alt, gorseller))
            yollar.append(f"/tur/{tur_slug(tur)}/")

    for t in tesisler:
        s_t = tesis_slug(t)
        if konumlar.get(s_t):
            slug_tesis = {tesis_slug(x): x for x in tesisler}
            komsular = [
                (slug_tesis[sl], km)
                for sl, km in en_yakinlar(s_t, konumlar, 3)
                if sl in slug_tesis
            ]
        else:
            komsular = [k for k in il_grup[t["il"]] if k is not t][:3]
        yaz(f"/tesis/{tesis_slug(t)}/",
            tesis_sayfasi(t, gorseller, komsular, konumlar.get(tesis_slug(t))))
        yollar.append(f"/tesis/{tesis_slug(t)}/")

    # arama dizini — [ad, ilce, il, slug, tur kisaltmasi]
    tur_kod = {k: i for i, k in enumerate(TURLER)}
    dizin = [
        [kisa_ad(t["ad"]), t["ilce"], t["il"], tesis_slug(t), tur_kod[t["tur"]],
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
            hnoktalar.append([k["lat"], k["lon"], kisa_ad(t["ad"]), tesis_slug(t), t["il"],
                              t["ilce"], tur_kod2[t["tur"]], 1 if t.get("deniz") else 0,
                              1 if k["kesinlik"] == "tesis" else 0])
        (CIKTI / "data" / "harita.json").write_text(
            json.dumps({"turler": list(TURLER), "t": hnoktalar}, ensure_ascii=False,
                       separators=(",", ":")), "utf-8")

    if konumlar:
        tk = {k: i for i, k in enumerate(TURLER)}
        satirlar = []
        for t in tesisler:
            k = konumlar.get(tesis_slug(t))
            if not k:
                continue
            satirlar.append([
                tesis_slug(t), kisa_ad(t["ad"]), t["il"], t["ilce"], tk[t["tur"]],
                k["lat"], k["lon"], t.get("deniz") or 0,
                1 if any("havuz" in o.lower() for o in t.get("olanaklar") or []) else 0,
                t.get("fiyat_2026") or "", fiyat_taban(t.get("fiyat_2026")),
                (t.get("telefon") or [""])[0],
                ", ".join(t.get("olanaklar") or []),
            ])
        (CIKTI / "data" / "tesis-tam.json").write_text(
            json.dumps({"turler": list(TURLER),
                        "iller": {a: [round(b[0], 5), round(b[1], 5)]
                                  for a, b in il_merkezleri(konumlar).items()},
                        "t": satirlar},
                       ensure_ascii=False, separators=(",", ":")), "utf-8")

    # ---- gezi rehberi ----
    gyol = KOK / "data" / "gezi.json"
    if gyol.exists() and konumlar:
        from genel import TARIH_TR

        gezi = json.loads(gyol.read_text("utf-8"))
        il_ilce: dict[str, dict[str, list]] = defaultdict(dict)
        etiket_kayit: dict[str, list] = defaultdict(list)
        for anahtar, yerler in gezi.items():
            il, _, ilce = anahtar.partition("|")
            temiz = temiz_yerler(yerler)
            if len(temiz) < 2:
                continue
            il_ilce[il][ilce] = temiz
            for y in temiz:
                etiket_kayit[y["tur"]].append((il, ilce, y))

        il_ilce_tesis: dict[tuple[str, str], list] = defaultdict(list)
        for t in tesisler:
            il_ilce_tesis[(t["il"], t["ilce"])].append(t)

        toplam_yer = 0
        for il, ilceler in il_ilce.items():
            for ilce, yerler in ilceler.items():
                yaz(
                    f"/gezi/{slug(il)}/{slug(ilce)}/",
                    ilce_sayfasi(il, ilce, yerler, il_ilce_tesis[(il, ilce)],
                                 gorseller, konumlar, TARIH_TR),
                )
                yollar.append(f"/gezi/{slug(il)}/{slug(ilce)}/")
                toplam_yer += len(yerler)
            yaz(f"/gezi/{slug(il)}/",
                il_gezi_sayfasi(il, ilceler, il_grup[il], gorseller, konumlar, TARIH_TR))
            yollar.append(f"/gezi/{slug(il)}/")

        yaz("/gezi/", gezi_dizini({i: sum(len(v) for v in d.values())
                                   for i, d in il_ilce.items()}, toplam_yer, TARIH_TR))
        yollar.append("/gezi/")

        for tur, kayitlar in etiket_kayit.items():
            if tur in ETIKET and len(kayitlar) >= 5:
                yaz(f"/etiket/{tur}/", etiket_sayfasi(tur, kayitlar, TARIH_TR))
                yollar.append(f"/etiket/{tur}/")
        etiket_sayi = {t: len(k) for t, k in etiket_kayit.items()
                       if t in ETIKET and len(k) >= 5}
        etiket_il = {t: len({il for il, _, _ in etiket_kayit[t]}) for t in etiket_sayi}
        if etiket_sayi:
            yaz("/etiket/", etiket_dizini(etiket_sayi, etiket_il))
            yollar.append("/etiket/")
        print(f"gezi: {len(il_ilce)} il, "
              f"{sum(len(v) for v in il_ilce.values())} ilçe, {toplam_yer} yer")
    else:
        import parca as _p

        _p.GEZ = [g for g in _p.GEZ if g[0] != "/gezi/"]

    # ---- açık veri sayfası ----
    from genel import TARIH_TR as _tarih

    yaz("/veri/", veri_sayfasi(tesisler, len(yollar) + 1, _tarih))
    yollar.append("/veri/")

    # ---- besleme, tarayıcı araması, uygulama tanımı, IndexNow ----
    from datetime import datetime, timezone

    simdi = datetime.now(timezone.utc)
    one_cikan = [
        ("/", f"{AD} — 81 ilde {len(tesisler)} tesis",
         "Türkiye'nin kamu konaklama tesislerinin bağımsız dizini."),
        ("/deniz/", "Denize yakın kamu tesisleri",
         "Denize konumu doğrulanmış tesislerin tam listesi."),
        ("/araclar/en-yakin/", "Bana en yakın kamu tesisi",
         "Bulunduğunuz ile göre en yakın tesisleri mesafe sırasıyla bulun."),
        ("/araclar/tatil-butcesi/", "Tatil bütçesi hesaplayıcı",
         "Konaklama, yakıt ve harcamayı birlikte hesaplayın."),
        ("/harita/", "Kamu misafirhaneleri haritası",
         "561 tesis harita üzerinde."),
        ("/veri/", "Açık veri — CC BY 4.0",
         "Veri kümesini indirin, kaynak göstererek kullanın."),
    ]
    for anahtar, baslik, ikon in REHBERLER:
        one_cikan.append((f"/rehber/{anahtar}/", baslik, ""))
    (CIKTI / "feed.xml").write_text(rss(one_cikan, simdi), "utf-8")
    (CIKTI / "opensearch.xml").write_text(opensearch(), "utf-8")
    (CIKTI / "manifest.webmanifest").write_text(manifest(), "utf-8")
    (CIKTI / f"{INDEXNOW_ANAHTAR}.txt").write_text(INDEXNOW_ANAHTAR, "utf-8")
    # IndexNow'a gönderilecek adres listesi
    (CIKTI / "urls.txt").write_text("\n".join(SITE + y for y in yollar), "utf-8")

    (CIKTI / "sitemap.xml").write_text(sitemap(yollar), "utf-8")
    (CIKTI / "robots.txt").write_text(robots(), "utf-8")
    (CIKTI / "llms.txt").write_text(llms_txt(tesisler, il_grup), "utf-8")
    shutil.copy(KOK / "tesisler.json", CIKTI / "tesisler.json")
    shutil.copy(KOK / "favicon.svg", CIKTI / "favicon.svg")
    shutil.copytree(KOK / "static", CIKTI / "static", dirs_exist_ok=True)
    # Yazi tipleri sayfa agirliginin %42'siydi; latin-ext dosyalari
    # sayfalarda gercekten gecen harflere indirilir (kaynak tam kalir).
    yazitipi.uygula(KOK, CIKTI)
    (CIKTI / "static" / "s.css").unlink(missing_ok=True)
    shutil.copytree(KOK / "img", CIKTI / "img")

    boyut = sum(f.stat().st_size for f in CIKTI.rglob("*") if f.is_file())
    print(f"{len(yollar)} sayfa · {len(list(CIKTI.rglob('*.html')))} html "
          f"· {boyut / 1024 / 1024:.1f} MB -> {CIKTI}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
