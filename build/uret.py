"""tesisler.json -> statik site.

Her sayfa üç şeyi birlikte taşır:
  1. İnsan için okunur içerik ve tek net eylem (ara / yol tarifi / yaz).
  2. Arama motoru için schema.org işaretlemesi, kırıntı, kanonik.
  3. Üretken arama motorları (GEO) için baştaki doğrudan cevap paragrafı,
     somut sayılar ve tablo — bunlar alıntılanan biçimlerdir.
"""

from __future__ import annotations

import json
import shutil
import sys
from collections import defaultdict
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from parca import (  # noqa: E402
    AD,
    google_yer_url,
    harita_kutusu,
    osm_adres,
    SITE,
    e,
    eylemler,
    ik,
    il_karti,
    kabuk,
    olanak_ikonlari,
    tesis_karti,
    yol_tarifi_url,
)
from mesafe import cikis_mesafeleri, sure_metni  # noqa: E402
from veri import cikma  # noqa: E402
from veri import TURLER, kisa_ad, sayfa_basligi, slug, tesis_slug, tur_slug  # noqa: E402

KOK = Path(__file__).resolve().parent.parent
CIKTI = KOK / "site"
BUGUN = date.today().isoformat()

KURUM_TAM = {
    "MEB": "Millî Eğitim Bakanlığı",
    "EGM": "Emniyet Genel Müdürlüğü",
    "DSİ": "Devlet Su İşleri Genel Müdürlüğü",
    "TKİ": "Türkiye Kömür İşletmeleri Kurumu",
    "İLKSAN": "İlkokul Öğretmenleri Sağlık ve Sosyal Yardım Sandığı",
}

# --------------------------------------------------------------------------
# Metin üretimi
# --------------------------------------------------------------------------


def kurum_tam(k: str) -> str:
    return KURUM_TAM.get(k, k)


def ozet_metni(t: dict) -> str:
    """Sayfanın ilk paragrafı: tek başına okunduğunda da tam cevap verir."""
    tur = t["tur"].lower()
    c = [
        f'<strong>{e(t["ad"])}</strong>, {e(t["il"])} ilinin {e(t["ilce"])} '
        f'ilçesinde bulunan ve {e(kurum_tam(t["kurum"]))} bünyesinde hizmet veren '
        f"bir {e(tur)}dir."
    ]
    tel = (t.get("telefon") or [None])[0]
    if tel:
        c.append(
            f"Müsaitlik, oda durumu ve güncel fiyat için tesis doğrudan "
            f'<strong>{e(tel)}</strong> numarasından aranır.'
        )
    if t.get("fiyat_2026"):
        c.append(f'Tesisin yayımladığı 2026 fiyatları: {e(t["fiyat_2026"])}.')
    else:
        c.append(
            "Tesisin yayımlanmış bir fiyat listesine ulaşılamadı; fiyat bilgisi "
            "telefonla alınmalıdır."
        )
    if t.get("deniz"):
        c.append(f'Denize konumu: {e(t["deniz"])}.')
    elif t.get("kiyi"):
        c.append(f'{e(t["il"])} kıyı ilidir; tesisin denize uzaklığı telefonla teyit edilmelidir.')
    if t.get("ankara_saat"):
        c.append(
            f'Ankara\'dan karayoluyla yaklaşık <strong>{e(t["ankara_saat"])} saat</strong> sürer.'
        )
    if t.get("not"):
        c.append(e(t["not"]))
    return " ".join(c)


def sss_listesi(t: dict) -> list[tuple[str, str]]:
    ad = t["ad"]
    tel = (t.get("telefon") or [None])[0]
    s: list[tuple[str, str]] = []

    kim = {
        "Öğretmenevi": (
            "Öğretmenevleri öncelikle Millî Eğitim Bakanlığı personeline hizmet verir. "
            "Boşluk durumuna göre diğer kamu personeli ve emeklileri ile birinci derece "
            "yakınları da konaklayabilir; öncelik ve fiyat farkı tesise göre değişir. "
            "Kesin bilgi için tesisin kendisi aranmalıdır."
        ),
        "Polisevi": (
            "Polisevleri öncelikle Emniyet Teşkilatı mensuplarına ve emeklilerine "
            "hizmet verir. Boşluk varsa diğer kamu personeli de konaklayabilir; "
            "uygulama tesisten tesise değişir."
        ),
        "Üniversite Misafirhanesi": (
            "Üniversite misafirhaneleri öncelikle kendi akademik ve idari personeline, "
            "ardından diğer üniversite ve kamu personeline açıktır. Kontenjan ve fiyat "
            "üniversitenin kendi yönergesine göre belirlenir."
        ),
        "Kamu Misafirhanesi": (
            "Kamu misafirhaneleri öncelikle bağlı bulundukları kurumun personeline, "
            "boşluk durumuna göre diğer kamu görevlilerine açıktır."
        ),
    }[t["tur"]]
    s.append((f"{ad} kimlere açıktır?", kim))

    if tel:
        hepsi = ", ".join(t["telefon"])
        s.append(
            (
                f"{ad} telefon numarası nedir?",
                f"{ad} telefon numarası {hepsi}. Rezervasyon yalnızca tesis "
                "üzerinden yapılır; bu sitede rezervasyon alınmamaktadır.",
            )
        )

    if t.get("fiyat_2026"):
        s.append(
            (
                f"{ad} 2026 fiyatları ne kadar?",
                f"Tesisin yayımladığı 2026 fiyatları şöyledir: {t['fiyat_2026']}. "
                "Fiyatlar kurum tarafından yıl içinde güncellenebilir; ödeme öncesi "
                "telefonla teyit edilmelidir.",
            )
        )
    else:
        s.append(
            (
                f"{ad} fiyatları ne kadar?",
                f"{ad} için yayımlanmış güncel bir fiyat listesine ulaşılamadı. "
                "Bu sitede tahmini fiyat yazılmaz; güncel fiyat "
                + (f"{tel} numarasından" if tel else "tesisten")
                + " öğrenilebilir.",
            )
        )

    if t.get("deniz"):
        s.append(
            (
                f"{ad} denize yakın mı?",
                f"Evet. Tesisin denize konumu: {t['deniz']}.",
            )
        )

    if t.get("ankara_saat"):
        s.append(
            (
                f"Ankara'dan {ad} ne kadar sürer?",
                f"Ankara'dan {t['ilce']}/{t['il']} istikametine karayoluyla yaklaşık "
                f"{t['ankara_saat']} saatlik yol vardır. Süre güzergâh ve trafiğe göre değişir.",
            )
        )
    return s


def sss_html(sss: list[tuple[str, str]]) -> str:
    ic = "".join(
        f"<details><summary>{e(s)}</summary><div class=\"cvp\"><p>{e(c)}</p></div></details>"
        for s, c in sss
    )
    return f'<div class="sss">{ic}</div>'


def sss_ld(sss: list[tuple[str, str]]) -> dict:
    return {
        "@context": "https://schema.org",
        "@type": "FAQPage",
        "mainEntity": [
            {
                "@type": "Question",
                "name": s,
                "acceptedAnswer": {"@type": "Answer", "text": c},
            }
            for s, c in sss
        ],
    }


def kirinti_ld(ogeler: list[tuple[str, str]]) -> dict:
    return {
        "@context": "https://schema.org",
        "@type": "BreadcrumbList",
        "itemListElement": [
            {"@type": "ListItem", "position": i, "name": a, "item": SITE + u}
            for i, (u, a) in enumerate(ogeler, 1)
        ],
    }


# --------------------------------------------------------------------------
# Tesis sayfası
# --------------------------------------------------------------------------


def tesis_sayfasi(t: dict, gorseller: dict, komsular: list,
                  konum: dict | None = None) -> str:
    s = tesis_slug(t)
    yol = f"/tesis/{s}/"
    g = gorseller.get(t["il"])
    tur_ad, kisa_tur, ikon, tur_aciklama = TURLER[t["tur"]]

    kirintilar = [
        ("/", "Ana sayfa"),
        (f"/il/{slug(t['il'])}/", t["il"]),
        (yol, kisa_ad(t["ad"])),
    ]

    hero_img = ""
    foto_not = ""
    if g:
        hero_img = (
            f'<img src="/img/il/{g["lg"]}" width="1200" height="675" '
            f'fetchpriority="high" decoding="async" '
            f'alt="{e(t["il"])} ilinden bir görünüm">'
        )
        foto_not = (
            f'<a class="foto-not" href="{e(g["sayfa"])}" target="_blank" rel="noopener nofollow">'
            f'{e(t["il"])} fotoğrafı · {e(g["yazar"])[:46]} · {e(g["lisans"])}</a>'
        )

    rozetler = [f'<span class="rz">{ik(ikon)}{e(kisa_tur)}</span>']
    if t.get("deniz"):
        rozetler.append(f'<span class="rz rz-deniz">{ik("deniz")}Denize yakın</span>')
    if t.get("fiyat_2026"):
        rozetler.append(f'<span class="rz">{ik("para")}Fiyat yayımlanmış</span>')
    if t.get("ankara_saat"):
        rozetler.append(f'<span class="rz">{ik("saat")}Ankara {e(t["ankara_saat"])} sa</span>')

    # künye tablosu — GEO: tablolar alıntılanır
    satirlar = []
    if kisa_ad(t["ad"]) != t["ad"]:
        satirlar.append(("Resmî ad", e(t["ad"])))
    satirlar += [
        ("Tesis türü", e(t["tur"])),
        ("Bağlı kurum", e(kurum_tam(t["kurum"]))),
        ("İl / ilçe", f'<a href="/il/{slug(t["il"])}/">{e(t["il"])}</a> / {e(t["ilce"])}'),
    ]
    adres = osm_adres(konum)
    if adres:
        satirlar.append(("Adres", f"{e(adres)} <span style=\"color:var(--soluk)\">"
                                  "(OpenStreetMap kaydı)</span>"))
    if t.get("telefon"):
        satirlar.append(
            (
                "Telefon",
                "<br>".join(
                    f'<a href="tel:+9{n.replace(" ", "").lstrip("0")}">{e(n)}</a>'
                    for n in t["telefon"]
                ),
            )
        )
    if t.get("eposta"):
        satirlar.append(("E-posta", f'<a href="mailto:{e(t["eposta"])}">{e(t["eposta"])}</a>'))
    if t.get("fiyat_2026"):
        satirlar.append(("2026 fiyatı", e(t["fiyat_2026"])))
    if t.get("deniz"):
        satirlar.append(("Denize konumu", e(t["deniz"])))
    if t.get("ankara_saat"):
        satirlar.append(("Ankara'dan süre", f'yaklaşık {e(t["ankara_saat"])} saat (karayolu)'))
    satirlar.append(
        (
            "Bilgi kaynağı",
            f'<a href="{e(t["kaynak"])}" target="_blank" rel="noopener nofollow">'
            f'{ik("dis")} kurum sayfası</a>',
        )
    )
    kunye = (
        '<table class="kunye"><tbody>'
        + "".join(f"<tr><th>{b}</th><td>{d}</td></tr>" for b, d in satirlar)
        + "</tbody></table>"
    )

    olanak = olanak_ikonlari(t.get("olanaklar"))
    olanak_html = ""
    if olanak:
        olanak_html = (
            f'<h2>Tesis olanakları</h2><ul class="ol ol-buyuk">'
            + "".join(f"<li>{ik(i)}{e(m)}</li>" for i, m in olanak)
            + "</ul>"
        )

    sss = sss_listesi(t)

    if konum:
        harita_html = harita_kutusu(
            ozellikler=(
                f'data-lat="{konum["lat"]}" data-lon="{konum["lon"]}" '
                f'data-kesinlik="{konum["kesinlik"]}" data-ad="{e(t["ad"])}"'
            ),
            sinif="harita-yan",
            aciklama=False,
        )
        konum_notu = (
            f'{t["ilce"]}, {t["il"]} — konum OpenStreetMap kaydından alındı.'
            if konum["kesinlik"] == "tesis"
            else f'{t["ilce"]}, {t["il"]} — harita ilçe merkezini gösterir, '
            "tesisin tam konumu değildir."
        )
    else:
        harita_html = ""
        konum_notu = f'{t["ilce"]}, {t["il"]} — tam adres için tesisi arayın.'

    mesafe_kutusu = ""
    mesafe_cumlesi = ""
    if konum:
        satirlar_m = cikis_mesafeleri(konum)
        if satirlar_m:
            govde_m = "".join(
                f"<tr><th>{e(sehir)}</th><td><b>{km} km</b></td>"
                f"<td>{e(sure_metni(saat))}</td></tr>"
                for sehir, km, saat in satirlar_m
            )
            mesafe_kutusu = (
                '<div class="kutu"><h3>Nereden ne kadar?</h3>'
                f'<table class="mesafe-tablo"><tbody>{govde_m}</tbody></table>'
                '<p style="font-size:.79rem;color:var(--soluk);margin:11px 0 12px">'
                "Koordinatlardan hesaplanan tahmini karayolu mesafesi ve mola hariç "
                "sürüş süresi.</p>"
                '<a class="dg dg-2 dg-sm dg-blok" href="/araclar/mesafe/">'
                f'{ik("yol")}Kendi ilinden hesapla</a></div>'
            )
            mesafe_cumlesi = " " + " ".join(
                f"{cikma(sehir)} yaklaşık {km} km ({sure_metni(saat)} sürüş) "
                "uzaklıkta."
                for sehir, km, saat in satirlar_m[:2]
            )

    komsu_html = ""
    if komsular:
        kartlar_k = "".join(
            tesis_karti(k, gorseller) if isinstance(k, dict) else tesis_karti(k[0], gorseller)
            for k in komsular
        )
        mesafeli = all(not isinstance(k, dict) for k in komsular)
        if mesafeli:
            en_yakin_metni = ", ".join(
                f"{kisa_ad(k[0]['ad'])} ({k[1]} km)" for k in komsular[:3]
            )
            alt_metin = f"Mesafeye göre en yakın olanlar: {en_yakin_metni}."
        else:
            alt_metin = "Aynı ildeki diğer kamu konaklama tesisleri."
        komsu_html = (
            f'<section class="bl bl-cizgi"><div class="bl-bas"><div>'
            f"<h2>Bu tesise en yakın diğer tesisler</h2>"
            f"<p>{e(alt_metin)}</p></div>"
            f'<a class="dg dg-2 dg-sm" href="/il/{slug(t["il"])}/">'
            f'{e(t["il"])} tesisleri{ik("ok")}</a></div>'
            f'<div class="iz">{kartlar_k}</div></section>'
        )

    icerik = f"""<div class="ts-ust">{hero_img}{foto_not}<div class="kap">
<div class="rzs">{"".join(rozetler)}</div>
<h1>{e(kisa_ad(t["ad"]))}</h1>
<p class="yer">{ik("konum")}{e(t["ilce"])}, {e(t["il"])}</p>
</div></div>
<div class="kap ikili">
<div>
<p class="ozet">{ozet_metni(t)}{mesafe_cumlesi}</p>
<h2 class="gizli">Künye</h2>
{kunye}
{olanak_html}
<h2 style="margin-top:2em">Sık sorulan sorular</h2>
{sss_html(sss)}
<div class="not" style="margin-top:22px">{ik("uyari")}<div>
<strong>Bu site rezervasyon almaz.</strong> Bilgiler kurumların kendi yayınlarından
derlenmiştir ve değişebilir. Yola çıkmadan önce tesisi telefonla arayın.</div></div>
</div>
<aside class="yan">
<div class="kutu kutu-vurgu">
<h2>İletişim</h2>
<div style="display:grid;gap:8px">{eylemler(t, buyuk=True)}</div>
</div>
{mesafe_kutusu}
<div class="kutu">
<h3>{e(tur_ad)} hakkında</h3>
<p style="font-size:.93rem;color:var(--soluk);margin:0 0 12px">{e(tur_aciklama)}</p>
<a class="dg dg-2 dg-sm dg-blok" href="/tur/{tur_slug(t["tur"])}/">
Tüm {e(tur_ad.lower())}{ik("ok")}</a>
</div>
<div class="kutu">
<h3>Konum</h3>
{harita_html}
<p style="font-size:.88rem;color:var(--soluk);margin:12px 0 12px">{konum_notu}</p>
<a class="dg dg-2 dg-sm dg-blok" href="{e(yol_tarifi_url(t))}"
target="_blank" rel="noopener nofollow">{ik("yol")}Google Haritalar'da aç</a>
<a class="dg dg-3 dg-sm dg-blok" style="margin-top:6px" href="{e(google_yer_url(t))}"
target="_blank" rel="noopener nofollow">{ik("yildiz")}Google yorumlarını gör</a>
</div>
</aside>
</div>
{komsu_html}"""

    ld_tesis: dict = {
        "@context": "https://schema.org",
        "@type": "LodgingBusiness",
        "@id": SITE + yol + "#tesis",
        "name": t["ad"],
        "url": SITE + yol,
        "address": {
            "@type": "PostalAddress",
            "addressLocality": t["ilce"],
            "addressRegion": t["il"],
            "addressCountry": "TR",
        },
        "parentOrganization": {
            "@type": "GovernmentOrganization",
            "name": kurum_tam(t["kurum"]),
        },
        "isAccessibleForFree": False,
        "sameAs": [t["kaynak"]],
        "speakable": {
            "@type": "SpeakableSpecification",
            "cssSelector": [".ozet", "h1"],
        },
    }
    if t.get("telefon"):
        ld_tesis["telephone"] = "+9" + t["telefon"][0].replace(" ", "").lstrip("0")
    if t.get("eposta"):
        ld_tesis["email"] = t["eposta"]
    if g:
        ld_tesis["image"] = f"{SITE}/img/il/{g['lg']}"
    if adres:
        ld_tesis["address"]["streetAddress"] = adres
    if konum and konum["kesinlik"] == "tesis":
        ld_tesis["geo"] = {
            "@type": "GeoCoordinates",
            "latitude": konum["lat"],
            "longitude": konum["lon"],
        }
    if olanak:
        ld_tesis["amenityFeature"] = [
            {"@type": "LocationFeatureSpecification", "name": m, "value": True}
            for _, m in olanak
        ]

    return kabuk(
        baslik=sayfa_basligi(t),
        aciklama=(
            f"{kisa_ad(t['ad'])} ({t['ilce']}, {t['il']}) telefon numarası, "
            + (f"2026 fiyatları, " if t.get("fiyat_2026") else "")
            + f"kimlerin kalabildiği ve yol tarifi. {kurum_tam(t['kurum'])} tesisi."
        )[:158],
        yol=yol,
        icerik=icerik,
        og_gorsel=f"/img/il/{g['lg']}" if g else None,
        kirintilar=kirintilar,
        harita=bool(konum),
        jsonld=[ld_tesis, sss_ld(sss), kirinti_ld(kirintilar)],
    )


# --------------------------------------------------------------------------
# İl sayfası
# --------------------------------------------------------------------------


def il_sayfasi(il: str, tesisler: list[dict], gorseller: dict,
               haritali: bool = False) -> str:
    yol = f"/il/{slug(il)}/"
    g = gorseller.get(il)
    deniz = [t for t in tesisler if t.get("deniz")]
    fiyatli = [t for t in tesisler if t.get("fiyat_2026")]
    turler = defaultdict(list)
    for t in tesisler:
        turler[t["tur"]].append(t)

    kirintilar = [("/", "Ana sayfa"), ("/il/", "İller"), (yol, il)]

    ozet = (
        f"<strong>{e(il)}</strong> ilinde bu dizinde kayıtlı "
        f"<strong>{len(tesisler)} kamu konaklama tesisi</strong> bulunuyor: "
        + ", ".join(f"{len(v)} {TURLER[k][0].lower()}" for k, v in sorted(turler.items()))
        + ". "
    )
    if deniz:
        ozet += f"Bunlardan {len(deniz)} tanesi denize yakın konumda. "
    if fiyatli:
        ozet += f"{len(fiyatli)} tesisin yayımlanmış 2026 fiyat listesi sayfasında yer alıyor. "
    ozet += (
        "Tesislerin tamamı telefonla doğrudan aranabilir; bu sitede rezervasyon alınmaz."
    )

    ilceler = sorted({t["ilce"] for t in tesisler})
    ozet += f" Tesisler {len(ilceler)} ilçeye yayılmış durumda."

    sss = [
        (
            f"{il}'de kaç kamu misafirhanesi var?",
            f"{il} ilinde bu dizinde kayıtlı {len(tesisler)} tesis bulunuyor: "
            + ", ".join(f"{len(v)} {TURLER[k][0].lower()}" for k, v in sorted(turler.items()))
            + f". Tesisler {len(ilceler)} farklı ilçede yer alıyor.",
        ),
        (
            f"{il}'de kamu misafirhanesi rezervasyonu nasıl yapılır?",
            f"{il} ilindeki tesislerde rezervasyon yalnızca tesisin kendi telefonundan "
            "yapılır; merkezî bir rezervasyon sistemi yoktur. Bu sayfadaki her tesis "
            "kartında telefon numarası ve arama düğmesi bulunur.",
        ),
    ]
    if deniz:
        sss.append(
            (
                f"{il}'de denize yakın hangi kamu tesisleri var?",
                f"{il} ilinde denize yakın konumda {len(deniz)} tesis kayıtlı: "
                + ", ".join(t["ad"] for t in deniz[:6])
                + ".",
            )
        )
    if fiyatli:
        sss.append(
            (
                f"{il}'de öğretmenevi fiyatları ne kadar?",
                "Yayımlanmış fiyat listesine ulaşılan tesisler: "
                + " | ".join(f"{t['ad']}: {t['fiyat_2026']}" for t in fiyatli[:4])
                + ". Diğer tesisler için fiyat telefonla öğrenilmelidir.",
            )
        )

    hero = ""
    if g:
        hero = (
            f'<img src="/img/il/{g["lg"]}" width="1200" height="675" fetchpriority="high" '
            f'decoding="async" alt="{e(il)} ilinden bir görünüm">'
            f'<a class="foto-not" href="{e(g["sayfa"])}" target="_blank" rel="noopener nofollow">'
            f'{e(g["yazar"])[:46]} · {e(g["lisans"])}</a>'
        )

    sirali = sorted(tesisler, key=lambda t: (not t.get("deniz"), not t.get("fiyat_2026"), t["ilce"]))
    kartlar = "".join(tesis_karti(t, gorseller, il_goster=False) for t in sirali)

    harita_bolum = ""
    if haritali:
        harita_bolum = (
            '<section class="bl kap bl-cizgi">'
            f'<div class="bl-bas"><div><h2>{e(il)} haritası</h2>'
            "<p>Tesislerin konumu. Bir kısmı OpenStreetMap kaydından, kalanı "
            "ilçe merkezinden gösterilir.</p></div></div>"
            + harita_kutusu(ozellikler=f'data-il="{e(il)}"', say_kimlik=True)
            + "</section>"
        )

    icerik = f"""<div class="ts-ust">{hero}<div class="kap">
<div class="rzs"><span class="rz">{ik("konum")}{len(ilceler)} ilçe</span>
<span class="rz">{ik("bina")}{len(tesisler)} tesis</span>
{f'<span class="rz rz-deniz">{ik("deniz")}{len(deniz)} denize yakın</span>' if deniz else ""}</div>
<h1>{e(il)} kamu misafirhaneleri</h1>
<p class="yer">{ik("bilgi")}Öğretmenevi, polisevi ve üniversite tesisleri</p>
</div></div>
<div class="kap" style="padding-top:26px">
<p class="ozet" style="max-width:78ch">{ozet}</p>
</div>
<section class="bl kap" style="padding-top:6px">
<div class="iz">{kartlar}</div>
</section>
{harita_bolum}
<section class="bl kap bl-cizgi">
<h2>{e(il)} hakkında sık sorulanlar</h2>
{sss_html(sss)}
</section>"""

    ld_liste = {
        "@context": "https://schema.org",
        "@type": "ItemList",
        "name": f"{il} kamu misafirhaneleri",
        "numberOfItems": len(tesisler),
        "itemListElement": [
            {
                "@type": "ListItem",
                "position": i,
                "url": f"{SITE}/tesis/{tesis_slug(t)}/",
                "name": t["ad"],
            }
            for i, t in enumerate(sirali, 1)
        ],
    }

    return kabuk(
        baslik=f"{il} Kamu Misafirhaneleri — {len(tesisler)} tesis, telefon ve fiyat",
        aciklama=(
            f"{il} ilindeki {len(tesisler)} öğretmenevi, polisevi ve kamu misafirhanesi. "
            f"Telefon numaraları, 2026 fiyatları"
            + (f", {len(deniz)} denize yakın tesis" if deniz else "")
            + ". Rezervasyon doğrudan tesisten."
        )[:158],
        yol=yol,
        icerik=icerik,
        og_gorsel=f"/img/il/{g['lg']}" if g else None,
        kirintilar=kirintilar,
        aktif="/il/",
        harita=haritali,
        jsonld=[ld_liste, sss_ld(sss), kirinti_ld(kirintilar)],
    )
