"""Gezi rehberi sayfaları: "X'te gezilecek yerler ve nerede kalınır".

Bu sayfaların değeri iki verinin kesişiminde: gezilecek yerler Vikipedi'den
(adı, konumu, özeti kaynaklı), konaklama ise bizim kendi veri kümemizden
(telefon, yayımlanmış fiyat, mesafe). İkisini birleştiren başka bir kaynak yok.

Hiçbir açıklama uydurulmaz. Vikipedi'de karşılığı olmayan yer listeye girmez;
mesafeler koordinatlardan hesaplanır ve tahmin oldukları yazılır.
"""

from __future__ import annotations

import re
from collections import defaultdict

from mesafe import CIKIS_NOKTALARI, karayolu_km, sure_metni, sure_saat
from parca import AD, SITE, e, ik, kabuk, tesis_karti
from veri import TURLER as TESIS_TURLERI
from veri import cikma, kisa_ad, slug, tesis_slug, yonelme

# Vikipedi'de yer alsa da gezilecek yer sayılmayanlar (toplama sırasında
# kaçanlar burada elenir; veri yeniden çekilmeden süzgeç sıkılaştırılabilir)
_ELE2 = re.compile(
    r"spor (salonu|tesis|kulüb)|tesisleri$|stadyum|okçuluk|yüzme havuzu|"
    r"kapalı spor|atletizm|hipodrom|fuar merkezi|kongre merkezi|"
    r"alışveriş merkezi|avm\b|iş merkezi|plaza|rezidans|toki\b|"
    r"sanayi sitesi|terminal|metro istasyonu|tramvay|teleferik hattı|"
    r"hastanesi|tıp fakültesi|araştırma hastanesi|devlet hastanesi",
    re.IGNORECASE,
)

# Etiket adları — gezi sayfalarındaki gruplama ve /etiket/ sayfaları
ETIKET = {
    "kale": ("Kaleler ve surlar", "kalkan"),
    "muze": ("Müzeler ve ören yerleri", "bina"),
    "cami": ("Camiler, medreseler ve türbeler", "bayrak"),
    "kilise": ("Kiliseler ve manastırlar", "bina"),
    "antik": ("Antik kentler", "bina"),
    "deniz": ("Deniz, sahil ve adalar", "deniz"),
    "doga": ("Doğa: şelale, mağara, göl ve yayla", "manzara"),
    "kopru": ("Tarihî köprüler", "yol"),
    "meydan": ("Meydanlar, çarşılar ve tarihî yapılar", "harita"),
    "diger": ("Görülecek diğer yerler", "yildiz"),
}


def temiz_yerler(yerler: list[dict]) -> list[dict]:
    return [y for y in yerler if not _ELE2.search(y["ad"])]


def _vikipedi(ad: str) -> str:
    import urllib.parse

    return "https://tr.wikipedia.org/wiki/" + urllib.parse.quote(ad.replace(" ", "_"))


def _yer_karti(y: dict) -> str:
    ikon = ETIKET.get(y["tur"], ETIKET["diger"])[1]
    aciklama = y.get("aciklama") or ""
    return f"""<article class="gz-k">
<div class="gz-bas"><span class="gz-km">{y["km"]}<small>km</small></span>
<div><h3>{e(y["ad"])}</h3>
{f'<span class="gz-tur">{ik(ikon)}{e(aciklama)}</span>' if aciklama else ""}</div></div>
<p>{e(y["ozet"])}</p>
<a class="gz-kaynak" href="{e(_vikipedi(y["ad"]))}" target="_blank" rel="noopener nofollow">
{ik("dis")}Vikipedi'de oku</a>
</article>"""


def _gruplu(yerler: list[dict]) -> str:
    grup: dict[str, list[dict]] = defaultdict(list)
    for y in yerler:
        grup[y["tur"]].append(y)
    sirali = sorted(grup.items(), key=lambda x: (-len(x[1]), x[0]))
    parcalar = []
    for tur, liste in sirali:
        ad, ikon = ETIKET.get(tur, ETIKET["diger"])
        parcalar.append(
            f'<h2 id="{tur}">{e(ad)} <span class="gz-say">{len(liste)}</span></h2>'
            f'<div class="gz-iz">{"".join(_yer_karti(y) for y in liste)}</div>'
        )
    return "".join(parcalar)


def _nasil_gidilir(konum: dict | None) -> tuple[str, str]:
    if not konum:
        return "", ""
    nokta = (konum["lat"], konum["lon"])
    satirlar, cumleler = [], []
    for ad, la, lo in CIKIS_NOKTALARI:
        km = karayolu_km(nokta, (la, lo))
        if km < 15:
            continue
        satirlar.append(
            f"<tr><th>{e(ad)}</th><td><b>{km} km</b></td>"
            f"<td>{e(sure_metni(sure_saat(km)))}</td></tr>"
        )
        cumleler.append(f"{cikma(ad)} yaklaşık {km} km")
    if not satirlar:
        return "", ""
    tablo = (
        '<table class="mesafe-tablo"><tbody>' + "".join(satirlar) + "</tbody></table>"
    )
    return tablo, ", ".join(cumleler)


def _sss_ortak(yer_adi: str, yerler: list[dict], tesisler: list[dict],
               mesafe_cumlesi: str) -> list[tuple[str, str]]:
    ilk_uc = ", ".join(y["ad"] for y in yerler[:3])
    sss = [
        (
            f"{yer_adi} gezilecek yerler nelerdir?",
            f"{yer_adi} çevresinde bu rehberde {len(yerler)} yer listeleniyor; "
            f"en yakınları {ilk_uc}. Listedeki her yerin adı, uzaklığı ve kısa "
            "tanımı Vikipedi kayıtlarından alınmıştır.",
        )
    ]
    if tesisler:
        adlar = ", ".join(kisa_ad(t["ad"]) for t in tesisler[:3])
        fiyatli = [t for t in tesisler if t.get("fiyat_2026")]
        cevap = (
            f"{yer_adi} ve çevresinde {len(tesisler)} kamu konaklama tesisi var: "
            f"{adlar}. Rezervasyon her tesisin kendi telefonundan yapılır."
        )
        if fiyatli:
            cevap += (
                f" {len(fiyatli)} tesisin yayımlanmış 2026 fiyatı sayfasında yer alıyor."
            )
        sss.append((f"{yer_adi} nerede kalınır? Kamu misafirhanesi var mı?", cevap))
    if mesafe_cumlesi:
        sss.append(
            (
                f"{yer_adi} nasıl gidilir?",
                f"Karayoluyla {mesafe_cumlesi} uzaklıkta. Süreler koordinatlardan "
                "hesaplanan tahminlerdir; ölçülmüş karayolu mesafesi değildir.",
            )
        )
    return sss


def _ld_yerler(yerler: list[dict], ad: str) -> dict:
    return {
        "@context": "https://schema.org",
        "@type": "ItemList",
        "name": f"{ad} gezilecek yerler",
        "numberOfItems": len(yerler),
        "itemListElement": [
            {
                "@type": "ListItem",
                "position": i,
                "item": {
                    "@type": "TouristAttraction",
                    "name": y["ad"],
                    "description": y["ozet"][:300],
                    "geo": {
                        "@type": "GeoCoordinates",
                        "latitude": y["lat"],
                        "longitude": y["lon"],
                    },
                    "sameAs": _vikipedi(y["ad"]),
                },
            }
            for i, y in enumerate(yerler[:40], 1)
        ],
    }


# --------------------------------------------------------------------------
def ilce_sayfasi(il: str, ilce: str, yerler: list[dict], tesisler: list[dict],
                 gorseller: dict, konumlar: dict, tarih: str) -> str:
    from uret import kirinti_ld, sss_html, sss_ld

    yol = f"/gezi/{slug(il)}/{slug(ilce)}/"
    g = gorseller.get(il)
    konum = next((konumlar.get(tesis_slug(t)) for t in tesisler
                  if konumlar.get(tesis_slug(t))), None)
    tablo, mesafe_cumlesi = _nasil_gidilir(konum)
    yer_adi = f"{ilce}, {il}" if ilce.lower() != il.lower() else il

    turler = sorted({y["tur"] for y in yerler})
    tur_ozet = ", ".join(
        f'<a href="/etiket/{t}/">{e(ETIKET[t][0].lower())}</a>' for t in turler[:4]
    )
    fiyatli = [t for t in tesisler if t.get("fiyat_2026")]

    ozet = (
        f"<strong>{e(yer_adi)}</strong> çevresinde, 10 kilometrelik yarıçapta "
        f"Vikipedi'de kaydı bulunan <strong>{len(yerler)} gezilecek yer</strong> "
        f"listelendi: {tur_ozet}. En yakını "
        f"<strong>{e(yerler[0]['ad'])}</strong> ({yerler[0]['km']} km). "
    )
    if tesisler:
        ozet += (
            f"Konaklama için ilçede {len(tesisler)} kamu tesisi var"
            + (f"; {len(fiyatli)} tanesinin yayımlanmış 2026 fiyatı biliniyor. "
               if fiyatli else ". ")
        )
    if mesafe_cumlesi:
        ozet += f"Karayoluyla {e(mesafe_cumlesi)} uzaklıkta."

    sss = _sss_ortak(yer_adi, yerler, tesisler, mesafe_cumlesi)
    kirintilar = [
        ("/", "Ana sayfa"),
        ("/gezi/", "Gezi rehberi"),
        (f"/gezi/{slug(il)}/", il),
        (yol, ilce),
    ]

    hero = ""
    if g:
        hero = (
            f'<img src="/img/il/{g["lg"]}" '
            f'srcset="/img/il/{g.get("md", g["lg"])} 800w, /img/il/{g["lg"]} 1200w" '
            f'sizes="100vw" width="1200" height="675" fetchpriority="high" '
            f'decoding="async" alt="{e(il)} ilinden bir görünüm">'
            f'<a class="foto-not" href="{e(g["sayfa"])}" target="_blank" rel="noopener nofollow">'
            f'{e(g["yazar"])[:44]} · {e(g["lisans"])}</a>'
        )

    konaklama = ""
    if tesisler:
        konaklama = (
            f'<section class="bl kap bl-cizgi"><div class="bl-bas"><div>'
            f"<h2>{e(yer_adi)} nerede kalınır?</h2>"
            f"<p>İlçedeki kamu konaklama tesisleri. Rezervasyon doğrudan tesisten "
            f"yapılır; bu sitede rezervasyon alınmaz.</p></div>"
            f'<a class="dg dg-2 dg-sm" href="/il/{slug(il)}/">{e(il)} tesisleri{ik("ok")}</a>'
            f'</div><div class="iz">'
            + "".join(tesis_karti(t, gorseller, il_goster=False) for t in tesisler)
            + "</div></section>"
        )

    icerik = f"""<div class="ts-ust">{hero}<div class="kap">
<div class="rzs"><span class="rz">{ik("harita")}Gezi rehberi</span>
<span class="rz">{ik("yildiz")}{len(yerler)} yer</span>
{f'<span class="rz">{ik("bina")}{len(tesisler)} kamu tesisi</span>' if tesisler else ""}</div>
<h1>{e(yer_adi)} gezilecek yerler</h1>
<p class="yer">{ik("konum")}Vikipedi kayıtlarından derlendi · 10 km yarıçap</p>
</div></div>
<div class="kap ikili">
<div>
<p class="ozet">{ozet}</p>
<div class="yazi">{_gruplu(yerler)}</div>
</div>
<aside class="yan">
{f'<div class="kutu"><h3>Nereden ne kadar?</h3>{tablo}<p style="font-size:.79rem;color:var(--soluk);margin:11px 0 0">Koordinatlardan hesaplanan tahmini karayolu mesafesi.</p></div>' if tablo else ""}
<div class="kutu kutu-vurgu">
<h3>Bu rehber nasıl hazırlandı?</h3>
<p style="font-size:.9rem;color:var(--orta);margin:0 0 12px">
Yerler, tesisin koordinatı çevresinde 10 km yarıçapta Vikipedi'de kaydı olan
noktalardan seçildi. Adlar, tanımlar ve özetler Vikipedi'den alınmıştır
(CC BY-SA 4.0). Uzaklıklar koordinatlardan hesaplandı.</p>
<a class="dg dg-2 dg-sm dg-blok" href="/gezi/{slug(il)}/">
{e(il)} geneli{ik("ok")}</a>
</div>
</aside>
</div>
{konaklama}
<section class="bl kap bl-cizgi"><h2>Sık sorulan sorular</h2>{sss_html(sss)}</section>"""

    return kabuk(
        baslik=f"{yer_adi} Gezilecek Yerler — {len(yerler)} yer ve konaklama",
        aciklama=(
            f"{yer_adi} çevresinde gezilecek {len(yerler)} yer: "
            + ", ".join(y["ad"] for y in yerler[:3])
            + (f". {len(tesisler)} kamu misafirhanesiyle konaklama." if tesisler else ".")
        )[:158],
        yol=yol,
        icerik=icerik,
        og_gorsel=f"/img/il/{g['lg']}" if g else None,
        on_gorsel=f"/img/il/{g.get('md', g['lg'])}" if g else "",
        on_srcset=(
            f"/img/il/{g.get('md', g['lg'])} 800w, /img/il/{g['lg']} 1200w"
            if g else ""
        ),
        anahtarlar=[
            f"{ilce} gezilecek yerler", f"{il} gezilecek yerler",
            f"{ilce} nerede kalınır", f"{ilce} {il} gezi rehberi",
            *[y["ad"] for y in yerler[:5]],
        ],
        kirintilar=kirintilar,
        aktif="/gezi/",
        jsonld=[
            _ld_yerler(yerler, yer_adi),
            {
                "@context": "https://schema.org",
                "@type": "TouristDestination",
                "name": yer_adi,
                "url": SITE + yol,
                "touristType": "Kamu personeli ve aileleri",
                "address": {
                    "@type": "PostalAddress",
                    "addressLocality": ilce,
                    "addressRegion": il,
                    "addressCountry": "TR",
                },
            },
            sss_ld(sss),
            kirinti_ld(kirintilar),
        ],
    )


def il_gezi_sayfasi(il: str, ilce_yerleri: dict[str, list[dict]],
                    tesisler: list[dict], gorseller: dict, konumlar: dict,
                    tarih: str) -> str:
    from uret import kirinti_ld, sss_html, sss_ld

    yol = f"/gezi/{slug(il)}/"
    g = gorseller.get(il)
    tum = [y for liste in ilce_yerleri.values() for y in liste]
    tum.sort(key=lambda y: y["km"])
    ilceler = sorted(ilce_yerleri, key=lambda i: -len(ilce_yerleri[i]))

    konum = next((konumlar.get(tesis_slug(t)) for t in tesisler
                  if konumlar.get(tesis_slug(t))), None)
    tablo, mesafe_cumlesi = _nasil_gidilir(konum)

    turler: dict[str, int] = defaultdict(int)
    for y in tum:
        turler[y["tur"]] += 1
    tur_ozet = ", ".join(
        f'{n} <a href="/etiket/{t}/">{e(ETIKET[t][0].lower())}</a>'
        for t, n in sorted(turler.items(), key=lambda x: -x[1])[:4]
    )

    ozet = (
        f"<strong>{e(il)}</strong> ilinde, kamu tesislerinin bulunduğu "
        f"{len(ilceler)} ilçe çevresinde Vikipedi'de kaydı bulunan "
        f"<strong>{len(tum)} gezilecek yer</strong> derlendi: {tur_ozet}. "
        f"İlde {len(tesisler)} kamu konaklama tesisi bulunuyor. "
    )
    if mesafe_cumlesi:
        ozet += f"İl merkezine karayoluyla {e(mesafe_cumlesi)} uzaklıkta."

    ilce_kartlari = "".join(
        f"""<a class="tur-k" href="/gezi/{slug(il)}/{slug(i)}/">
{ik("konum", "ik tur-ik")}<strong>{e(i)}</strong>
<span>{len(ilce_yerleri[i])} gezilecek yer</span>
<em>{e(", ".join(y["ad"] for y in ilce_yerleri[i][:3]))}</em>
<span class="tur-ok">{ik("ok")}</span></a>"""
        for i in ilceler
    )

    sss = _sss_ortak(il, tum, tesisler, mesafe_cumlesi)
    kirintilar = [("/", "Ana sayfa"), ("/gezi/", "Gezi rehberi"), (yol, il)]

    hero = ""
    if g:
        hero = (
            f'<img src="/img/il/{g["lg"]}" '
            f'srcset="/img/il/{g.get("md", g["lg"])} 800w, /img/il/{g["lg"]} 1200w" '
            f'sizes="100vw" width="1200" height="675" fetchpriority="high" '
            f'decoding="async" alt="{e(il)} ilinden bir görünüm">'
            f'<a class="foto-not" href="{e(g["sayfa"])}" target="_blank" rel="noopener nofollow">'
            f'{e(g["yazar"])[:44]} · {e(g["lisans"])}</a>'
        )

    icerik = f"""<div class="ts-ust">{hero}<div class="kap">
<div class="rzs"><span class="rz">{ik("harita")}Gezi rehberi</span>
<span class="rz">{ik("yildiz")}{len(tum)} yer</span>
<span class="rz">{ik("bina")}{len(tesisler)} kamu tesisi</span></div>
<h1>{e(il)} gezilecek yerler</h1>
<p class="yer">{ik("konum")}{len(ilceler)} ilçe · Vikipedi kayıtlarından derlendi</p>
</div></div>
<div class="kap" style="padding-top:26px"><p class="ozet" style="max-width:78ch">{ozet}</p></div>
<section class="bl kap" style="padding-top:6px">
<div class="bl-bas"><div><h2>İlçelere göre</h2>
<p>Kamu tesisi bulunan ilçeler ve çevrelerindeki gezilecek yerler.</p></div>
<a class="dg dg-2 dg-sm" href="/il/{slug(il)}/">{e(il)} tesisleri{ik("ok")}</a></div>
<div class="tur-iz">{ilce_kartlari}</div>
</section>
<section class="bl kap bl-cizgi">
<div class="bl-bas"><div><h2>{e(il)} ilinde öne çıkan yerler</h2>
<p>Tesislere en yakın olanlardan başlayarak.</p></div></div>
<div class="gz-iz">{"".join(_yer_karti(y) for y in tum[:12])}</div>
</section>
<section class="bl kap bl-cizgi"><h2>Sık sorulan sorular</h2>{sss_html(sss)}</section>"""

    return kabuk(
        baslik=f"{il} Gezilecek Yerler — {len(tum)} yer, {len(ilceler)} ilçe",
        aciklama=(
            f"{il} gezilecek yerler: {len(tum)} nokta, {len(ilceler)} ilçe. "
            + ", ".join(y["ad"] for y in tum[:3])
            + f". {len(tesisler)} kamu misafirhanesiyle konaklama."
        )[:158],
        yol=yol,
        icerik=icerik,
        og_gorsel=f"/img/il/{g['lg']}" if g else None,
        on_gorsel=f"/img/il/{g.get('md', g['lg'])}" if g else "",
        on_srcset=(
            f"/img/il/{g.get('md', g['lg'])} 800w, /img/il/{g['lg']} 1200w"
            if g else ""
        ),
        anahtarlar=[
            f"{il} gezilecek yerler", f"{il} gezi rehberi", f"{il} tarihi yerler",
            f"{il} nerede kalınır", f"{il} kamu misafirhanesi",
            *[y["ad"] for y in tum[:4]],
        ],
        kirintilar=kirintilar,
        aktif="/gezi/",
        jsonld=[_ld_yerler(tum, il), sss_ld(sss), kirinti_ld(kirintilar)],
    )


def gezi_dizini(il_ozet: dict[str, int], toplam_yer: int, tarih: str) -> str:
    from uret import kirinti_ld

    kirintilar = [("/", "Ana sayfa"), ("/gezi/", "Gezi rehberi")]
    satirlar = "".join(
        f'<li><a href="/gezi/{slug(il)}/">{e(il)}<span>{n}</span></a></li>'
        for il, n in sorted(il_ozet.items())
    )
    icerik = f"""<section class="bl kap">
<div class="bl-bas"><div><h1>Gezi rehberi</h1>
<p>Kamu tesislerinin çevresinde, 10 kilometrelik yarıçapta Vikipedi'de kaydı
bulunan <strong>{toplam_yer} gezilecek yer</strong>. {len(il_ozet)} il, kale ve
müzeden şelale ve antik kente kadar. Her yerin uzaklığı koordinatlardan
hesaplandı; her tanım Vikipedi'den alınıp kaynağı gösterildi.</p></div></div>
<ul class="il-liste">{satirlar}</ul>
</section>
<section class="bl kap bl-cizgi">
<div class="bl-bas"><div><h2>Konuya göre</h2>
<p>Aynı yerler türlerine göre gruplanmış hâlde.</p></div></div>
<div class="tur-iz">{"".join(
    f'<a class="tur-k" href="/etiket/{t}/">{ik(ikon, "ik tur-ik")}'
    f'<strong>{e(ad)}</strong><span class="tur-ok">{ik("ok")}</span></a>'
    for t, (ad, ikon) in ETIKET.items())}</div>
</section>"""
    return kabuk(
        baslik=f"Gezi Rehberi — {toplam_yer} gezilecek yer, {len(il_ozet)} il",
        aciklama=f"Türkiye'de {toplam_yer} gezilecek yer: kale, müze, antik kent, "
        "şelale ve sahiller. Her yerin yanında en yakın kamu misafirhanesi.",
        yol="/gezi/",
        icerik=icerik,
        kirintilar=kirintilar,
        aktif="/gezi/",
        jsonld=[kirinti_ld(kirintilar)],
    )


def etiket_dizini(sayilar: dict[str, int], iller: dict[str, int]) -> str:
    """/etiket/ kök sayfası: konu başlıklarının dizini.

    Alt sayfalar (/etiket/kale/ gibi) üretiliyordu ama kök adres boş kalıyor
    ve sunucu 403 dönüyordu: hem ziyaretçiye hem tarayıcıya kapalı bir düğüm.
    """
    from uret import kirinti_ld, sss_html, sss_ld

    kirintilar = [("/", "Ana sayfa"), ("/gezi/", "Gezi rehberi"), ("/etiket/", "Konular")]
    toplam = sum(sayilar.values())
    varlar = [(t, ETIKET[t]) for t in ETIKET if sayilar.get(t)]

    kartlar = "".join(
        f'<a class="tur-k" href="/etiket/{t}/">{ik(ikon, "ik tur-ik")}'
        f'<strong>{e(ad)}</strong>'
        f'<em>{sayilar[t]} yer · {iller.get(t, 0)} il</em>'
        f'<span class="tur-ok">{ik("ok")}</span></a>'
        for t, (ad, ikon) in varlar
    )

    sss = [
        ("Konu sayfaları neyi listeler?",
         f"Her konu sayfası, kamu tesislerinin 10 kilometrelik çevresinde Vikipedi'de "
         f"kaydı bulunan yerleri türlerine göre gruplar. Toplam {toplam} yer "
         f"{len(varlar)} konu başlığı altında toplanmıştır."),
        ("Uzaklıklar neye göre hesaplanıyor?",
         "Her yerin yanındaki kilometre, o ilçedeki kamu konaklama tesisine olan "
         "kuş uçuşu mesafedir; tesisin kendi koordinatından hesaplanır."),
    ]

    icerik = f"""<section class="bl kap">
<div class="bl-bas"><div><h1>Konu başlıkları</h1>
<p>Kamu tesislerinin çevresindeki <strong>{toplam} gezilecek yer</strong>,
{len(varlar)} konu başlığı altında gruplandı. Bir konu seçin, o türdeki yerleri
tesise uzaklığıyla birlikte görün.</p></div></div>
<div class="tur-iz" style="margin-top:24px">{kartlar}</div>
</section>
<section class="bl kap bl-cizgi">
<h2>Sık sorulan sorular</h2>{sss_html(sss)}</section>"""

    ld = {
        "@context": "https://schema.org",
        "@type": "ItemList",
        "name": "Gezilecek yer konuları",
        "numberOfItems": len(varlar),
        "itemListElement": [
            {"@type": "ListItem", "position": i, "name": ad,
             "url": f"{SITE}/etiket/{t}/"}
            for i, (t, (ad, _)) in enumerate(varlar, 1)
        ],
    }
    return kabuk(
        baslik=f"Konu Başlıkları — {toplam} gezilecek yer, {len(varlar)} konu",
        aciklama=f"Kale, müze, antik kent, sahil ve doğa: {toplam} gezilecek yer "
        f"{len(varlar)} konu başlığında. Her yerin en yakın kamu tesisine uzaklığı.",
        yol="/etiket/",
        icerik=icerik,
        kirintilar=kirintilar,
        aktif="/gezi/",
        jsonld=[ld, sss_ld(sss), kirinti_ld(kirintilar)],
    )


def etiket_sayfasi(tur: str, kayitlar: list[tuple[str, str, dict]],
                   tarih: str) -> str:
    """kayitlar: [(il, ilce, yer), ...]"""
    from uret import kirinti_ld, sss_html, sss_ld

    ad, ikon = ETIKET[tur]
    yol = f"/etiket/{tur}/"
    iller = sorted({il for il, _, _ in kayitlar})
    kayitlar = sorted(kayitlar, key=lambda x: x[2]["km"])[:120]

    ozet = (
        f"Bu sayfada <strong>{ad.lower()}</strong> başlığı altında toplanan "
        f"<strong>{len(kayitlar)} yer</strong> var; {len(iller)} ile yayılmış "
        "durumda. Her yerin yanındaki uzaklık, o ilçedeki kamu tesisine olan "
        "kuş uçuşu mesafedir — yani oraya yerleşirseniz ne kadar yakın olursunuz."
    )
    satirlar = "".join(
        f'<tr><td><a href="{e(_vikipedi(y["ad"]))}" target="_blank" '
        f'rel="noopener nofollow">{e(y["ad"])}</a></td>'
        f'<td><a href="/gezi/{slug(il)}/{slug(ilce)}/">{e(ilce)}, {e(il)}</a></td>'
        f'<td>{y["km"]} km</td><td>{e(y.get("aciklama") or "—")}</td></tr>'
        for il, ilce, y in kayitlar
    )
    sss = [
        (f"Türkiye'de gezilecek {ad.lower()} nerelerdedir?",
         f"Bu rehberde {ad.lower()} başlığı altında {len(kayitlar)} yer listeleniyor "
         f"ve bunlar {len(iller)} ile dağılmış durumda. En yakın örnekler: "
         + ", ".join(y["ad"] for _, _, y in kayitlar[:4]) + "."),
        ("Bu listedeki yerlerin yanında nerede kalınır?",
         "Her satırdaki ilçe bağlantısı, o ilçenin gezi sayfasına gider; orada "
         "ilçedeki kamu konaklama tesisleri telefon ve fiyatlarıyla listelenir."),
    ]
    kirintilar = [("/", "Ana sayfa"), ("/gezi/", "Gezi rehberi"),
                  ("/etiket/", "Konular"), (yol, ad)]
    icerik = f"""<section class="bl kap" style="max-width:1000px">
<span class="rz rz-vurgu">{ik(ikon)}Konu</span>
<h1 style="margin-top:10px">{e(ad)}</h1>
<p class="ozet" style="margin-top:18px">{ozet}</p>
<div class="yazi" style="margin-top:24px"><table>
<thead><tr><th>Yer</th><th>Nerede</th><th>Tesise uzaklık</th><th>Ne</th></tr></thead>
<tbody>{satirlar}</tbody></table></div>
</section>
<section class="bl kap bl-cizgi" style="max-width:1000px">
<h2>Sık sorulan sorular</h2>{sss_html(sss)}</section>"""
    return kabuk(
        baslik=f"{ad} — {len(kayitlar)} yer, {len(iller)} il",
        aciklama=f"Türkiye'de {ad.lower()}: {len(kayitlar)} yer, en yakın kamu "
        "misafirhanesine uzaklığıyla birlikte.",
        yol=yol,
        icerik=icerik,
        kirintilar=kirintilar,
        aktif="/gezi/",
        jsonld=[sss_ld(sss), kirinti_ld(kirintilar)],
    )
