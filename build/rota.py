"""Kamu misafirhanelerinde konaklayarak yapılabilecek çok duraklı rotalar.

Rotalar elle yazılmıyor, elimizdeki gerçek veriden üretiliyor:
  * duraklar, koordinatı doğrulanmış (kesinlik="tesis") tesisler,
  * her durakta o ilçenin Vikipedi kayıtlı gezilecek yerleri (data/gezi.json),
  * o ilin yöresel yemekleri (data/mutfak.json, yine Vikipedi),
  * mesafe ve süre build/mesafe.py ile, maliyet araçlardaki sabitlerle.

Zincirleme kuralı: iki durak arası bir günlük sürüşe sığmalı (70–220 km).
Bu sınır rotayı kendiliğinden bölgesel tutuyor; "Ege turu" diye elle
etiketlemeye gerek kalmıyor.

Maliyet TAHMİNDİR ve sayfada varsayımlarıyla birlikte yazılır. Konaklama
yalnızca tesisin kendi yayımladığı fiyat varsa hesaba girer; olmayan tesis
için uydurma tutar konmaz, "fiyatı yayımlanmamış" denir.
"""

from __future__ import annotations

import json
from pathlib import Path

from mesafe import karayolu_km, sure_metni, sure_saat
from parca import SITE, e, harita_kutusu, ik, kabuk
from veri import fiyat_taban, kisa_ad, slug, tesis_slug

KOK = Path(__file__).resolve().parent.parent

#: İki durak arası kabul edilen mesafe aralığı (km, karayolu tahmini)
EN_AZ_ADIM = 70
EN_COK_ADIM = 220
#: Bir rotadaki durak sayısı
EN_AZ_DURAK = 3
EN_COK_DURAK = 5
#: Durak sayılabilmesi için ilçede en az bu kadar gezilecek yer olmalı
EN_AZ_YER = 3
#: İki rota bu kadar durağı paylaşıyorsa ikincisi üretilmez
ORTAK_DURAK_SINIRI = 2

#: Maliyet varsayımları — araçlardaki (build/araclar.py) varsayılanlarla aynı
YAKIT_TUKETIM = 7.0     # L/100 km
YAKIT_FIYAT = 50.0      # TL/L
GUNLUK_HARCAMA = 600    # TL, kişi başı yeme-içme ve giriş ücretleri
KISI = 2                # örnek hesap iki kişilik


#: Marmara Denizi'nin kabaca sinirlari. Kus ucusu mesafeyi 1,27 ile carpan
#: tahmin, denizin uzerinden geciyorsa cok yaniliyor: Kirklareli'den
#: Balikesir'e gercek yol Istanbul uzerinden dolasir. Kuzeyi guneye baglayan
#: adimlar bu yuzden rotaya alinmiyor.
_MARMARA = (40.30, 41.00, 26.70, 29.90)  # min_lat, max_lat, min_lon, max_lon


def deniz_gecer(a: tuple[float, float], b: tuple[float, float]) -> bool:
    """İki nokta Marmara'nın iki yakasında mı?"""
    alt, ust, sol, sag = _MARMARA
    kuzey, guney = max(a[0], b[0]), min(a[0], b[0])
    if not (kuzey > ust and guney < alt):
        return False
    # Boylamlar denizin penceresine denk geliyorsa gercekten karsi kiyilar
    return sol <= a[1] <= sag and sol <= b[1] <= sag


def _yer_anahtari(t: dict) -> str:
    return f"{t['il']}|{t['ilce']}"


def duraklar(tesisler: list[dict], konumlar: dict, gezi: dict) -> list[dict]:
    """Rotaya girebilecek tesisler: koordinatı kesin ve çevresi gezilecek."""
    secilen = []
    for t in tesisler:
        k = konumlar.get(tesis_slug(t))
        if not k or k.get("kesinlik") != "tesis":
            continue
        yerler = gezi.get(_yer_anahtari(t)) or []
        if len(yerler) < EN_AZ_YER:
            continue
        secilen.append({
            "tesis": t,
            "slug": tesis_slug(t),
            "nokta": (k["lat"], k["lon"]),
            "yerler": yerler,
        })
    return secilen


def _zincir(baslangic: dict, havuz: list[dict], kullanilan: set[str]) -> list[dict]:
    """Bir duraktan başlayıp adım adım komşu durak ekler."""
    rota = [baslangic]
    il_sayaci = {baslangic["tesis"]["il"]: 1}
    secilenler = {baslangic["slug"]}

    while len(rota) < EN_COK_DURAK:
        son = rota[-1]
        adaylar = []
        for d in havuz:
            if d["slug"] in secilenler or d["slug"] in kullanilan:
                continue
            # Aynı il üst üste iki duraktan fazla olmasın: rota il değiştirsin
            if il_sayaci.get(d["tesis"]["il"], 0) >= 2:
                continue
            if deniz_gecer(son["nokta"], d["nokta"]):
                continue
            km = karayolu_km(son["nokta"], d["nokta"])
            if not (EN_AZ_ADIM <= km <= EN_COK_ADIM):
                continue
            # Yakın ve çok gezilecek yeri olan durak tercih edilir
            adaylar.append((-len(d["yerler"]), km, d))
        if not adaylar:
            break
        adaylar.sort(key=lambda x: (x[0], x[1]))
        secim = adaylar[0][2]
        rota.append(secim)
        secilenler.add(secim["slug"])
        il_sayaci[secim["tesis"]["il"]] = il_sayaci.get(secim["tesis"]["il"], 0) + 1
    return rota


def rotalar_uret(havuz: list[dict]) -> list[list[dict]]:
    """Gezilecek yeri en zengin duraklardan başlayarak rota zincirleri kurar."""
    sirali = sorted(havuz, key=lambda d: -len(d["yerler"]))
    uretilen: list[list[dict]] = []
    kullanilan: set[str] = set()

    for baslangic in sirali:
        if baslangic["slug"] in kullanilan:
            continue
        rota = _zincir(baslangic, havuz, kullanilan)
        if len(rota) < EN_AZ_DURAK:
            continue
        # Aynı durakları paylaşan ikinci bir rota üretme
        yeni = {d["slug"] for d in rota}
        if any(len(yeni & {x["slug"] for x in r}) > ORTAK_DURAK_SINIRI for r in uretilen):
            continue
        uretilen.append(rota)
        kullanilan |= yeni
    return uretilen


def rota_ozeti(rota: list[dict]) -> dict:
    """Mesafe, süre ve maliyet tahmini."""
    adimlar = []
    toplam_km = 0
    for onceki, sonraki in zip(rota, rota[1:]):
        km = karayolu_km(onceki["nokta"], sonraki["nokta"])
        toplam_km += km
        adimlar.append({
            "nereden": kisa_ad(onceki["tesis"]["ad"]),
            "nereye": kisa_ad(sonraki["tesis"]["ad"]),
            "km": km,
            "sure": sure_metni(sure_saat(km)),
        })

    gece = len(rota)  # her durakta bir gece
    fiyatlar = [fiyat_taban(d["tesis"].get("fiyat_2026")) for d in rota]
    yayimlanan = [f for f in fiyatlar if f]
    yakit = round(toplam_km * (YAKIT_TUKETIM / 100) * YAKIT_FIYAT)
    harcama = GUNLUK_HARCAMA * KISI * gece

    return {
        "adimlar": adimlar,
        "toplam_km": toplam_km,
        "toplam_sure": sure_metni(sure_saat(toplam_km)),
        "gece": gece,
        "yakit": yakit,
        "harcama": harcama,
        "konaklama": sum(yayimlanan),
        "fiyatli_durak": len(yayimlanan),
        "toplam": yakit + harcama + sum(yayimlanan),
    }


def rota_slug(rota: list[dict]) -> str:
    iller = []
    for d in rota:
        il = d["tesis"]["il"]
        if il not in iller:
            iller.append(il)
    return "-".join(slug(i) for i in iller[:3]) + f"-{len(rota)}-durak"


def rota_adi(rota: list[dict]) -> str:
    iller = []
    for d in rota:
        il = d["tesis"]["il"]
        if il not in iller:
            iller.append(il)
    if len(iller) == 1:
        return f"{iller[0]} içinde {len(rota)} duraklı rota"
    return " – ".join(iller) + f" rotası ({len(rota)} durak)"


def veriyi_yukle() -> tuple[dict, dict]:
    gezi_yolu = KOK / "data" / "gezi.json"
    mutfak_yolu = KOK / "data" / "mutfak.json"
    gezi = json.loads(gezi_yolu.read_text("utf-8")) if gezi_yolu.exists() else {}
    mutfak = json.loads(mutfak_yolu.read_text("utf-8")) if mutfak_yolu.exists() else {}
    return gezi, mutfak


# --------------------------------------------------------------------------
# Sayfalar
# --------------------------------------------------------------------------

def _tl(n: int) -> str:
    return f"{int(n):,}".replace(",", ".") + " TL"


def _yer_satirlari(durak: dict, adet: int = 5) -> str:
    yerler = sorted(durak["yerler"], key=lambda y: y["km"])[:adet]
    return "".join(
        f'<li><strong>{e(y["ad"])}</strong> <span class="rota-km">{y["km"]} km</span>'
        + (f'<em>{e(y["aciklama"])}</em>' if y.get("aciklama") else "")
        + "</li>"
        for y in yerler
    )


def _yemek_satirlari(il: str, mutfak: dict, adet: int = 5) -> str:
    yemekler = (mutfak.get(il) or [])[:adet]
    if not yemekler:
        return ""
    return "".join(
        f'<li><strong>{e(y["ad"])}</strong>'
        + (f'<em>{e(y["aciklama"] or y["ozet"][:90])}</em>' if (y.get("aciklama") or y.get("ozet")) else "")
        + "</li>"
        for y in yemekler
    )


def rota_sayfasi(rota: list[dict], mutfak: dict, gorseller: dict) -> str:
    """Tek rota sayfası: harita, duraklar, gezilecekler, yemekler, maliyet."""
    from uret import kirinti_ld, sss_html, sss_ld

    ad = rota_adi(rota)
    s_r = rota_slug(rota)
    yol = f"/rota/{s_r}/"
    ozet_v = rota_ozeti(rota)
    iller = []
    for d in rota:
        if d["tesis"]["il"] not in iller:
            iller.append(d["tesis"]["il"])

    harita_veri = json.dumps(
        [
            {
                "lat": d["nokta"][0], "lon": d["nokta"][1],
                "ad": kisa_ad(d["tesis"]["ad"]), "s": d["slug"],
                "yer": f'{d["tesis"]["ilce"]}, {d["tesis"]["il"]}',
            }
            for d in rota
        ],
        ensure_ascii=False,
    )

    duraklar_html = ""
    for i, d in enumerate(rota, 1):
        t = d["tesis"]
        fiyat = fiyat_taban(t.get("fiyat_2026"))
        yemekler = _yemek_satirlari(t["il"], mutfak)
        adim = ""
        if i > 1:
            a = ozet_v["adimlar"][i - 2]
            adim = (f'<p class="rota-adim">{ik("ok")} Önceki duraktan '
                    f'<strong>{a["km"]} km</strong> · yaklaşık {a["sure"]} sürüş</p>')
        duraklar_html += f"""{adim}
<article class="rota-durak">
<div class="rota-bas"><span class="rota-no">{i}</span>
<div><h3><a href="/tesis/{d["slug"]}/">{e(kisa_ad(t["ad"]))}</a></h3>
<p class="yer">{ik("konum")}{e(t["ilce"])}, {e(t["il"])} · {e(t["tur"])}</p></div></div>
<div class="rota-iki">
<div><h4>{ik("harita")}Bu durakta gezilecekler</h4>
<ul class="rota-liste">{_yer_satirlari(d)}</ul>
<a class="dg dg-2 dg-sm" href="/gezi/{slug(t["il"])}/{slug(t["ilce"])}/">
{e(t["ilce"])} gezi rehberi{ik("ok")}</a></div>
{f'<div><h4>{ik("bilgi")}{e(t["il"])} mutfağından</h4><ul class="rota-liste">{yemekler}</ul></div>' if yemekler else ""}
</div>
<p class="rota-fiyat">{
    f'Yayımlanmış 2026 fiyatı: <strong>{_tl(fiyat)}</strong> (en düşük oda tipi)'
    if fiyat else 'Bu tesis fiyatını yayımlamamış; güncel tutarı telefonla teyit edin.'
}</p>
</article>"""

    sss = [
        (f"{ad} kaç günlük?",
         f"Rota {len(rota)} durakta {ozet_v['gece']} gece konaklamayla planlandı. "
         f"Duraklar arası toplam {ozet_v['toplam_km']} km ve yaklaşık "
         f"{ozet_v['toplam_sure']} sürüş var; her durakta tam gün gezmek için "
         f"{len(rota) + 1} güne yaymak rahat olur."),
        ("Bu rotanın maliyeti ne kadar?",
         f"Yakıt {_tl(ozet_v['yakit'])} (7 L/100 km ve {int(YAKIT_FIYAT)} TL/litre "
         f"varsayımıyla), iki kişi için yeme-içme ve giriş "
         f"{_tl(ozet_v['harcama'])} ({GUNLUK_HARCAMA} TL/kişi/gün varsayımı). "
         + (f"Fiyatını yayımlamış {ozet_v['fiyatli_durak']} tesiste konaklama "
            f"{_tl(ozet_v['konaklama'])}. " if ozet_v["konaklama"] else
            "Duraklardaki tesislerin hiçbiri fiyatını yayımlamadığı için konaklama "
            "tutarı hesaba katılmadı. ")
         + "Varsayımları kendi aracınıza göre değiştirmek için tatil bütçesi "
           "aracını kullanabilirsiniz."),
        ("Bu tesislerde kimler kalabilir?",
         "Her tesis kendi kurumunun personeline ve birinci derece yakınlarına "
         "önceliklidir; boş kapasitede diğer kamu personeli, kimi tesislerde "
         "herkes konaklayabilir. Rezervasyon her tesisin kendi telefonundan "
         "yapılır, bu sitede rezervasyon alınmaz."),
    ]

    icerik = f"""<section class="bl kap">
<div class="bl-bas"><div>
<span class="rz rz-vurgu">{ik("harita")}{len(rota)} duraklı rota</span>
<h1 style="margin-top:10px">{e(ad)}</h1>
<p class="ozet" style="max-width:78ch">Bu rotanın her durağında bir kamu
misafirhanesinde kalınıyor. Toplam <strong>{ozet_v["toplam_km"]} km</strong>,
yaklaşık <strong>{ozet_v["toplam_sure"]}</strong> sürüş ve
<strong>{ozet_v["gece"]} gece</strong>. Gezilecek yerler Vikipedi kayıtlarından,
mesafeler tesislerin koordinatlarından hesaplandı.</p></div></div>
<div class="rzs" style="margin-top:18px">
<span class="rz">{ik("konum")}{ozet_v["toplam_km"]} km</span>
<span class="rz">{ik("bilgi")}{ozet_v["toplam_sure"]} sürüş</span>
<span class="rz">{ik("bina")}{ozet_v["gece"]} gece</span>
<span class="rz rz-vurgu">{ik("bilgi")}yaklaşık {_tl(ozet_v["toplam"])}</span>
</div>
</section>
<section class="bl kap">
{harita_kutusu(ozellikler=f"data-rota='{e(harita_veri)}'", aciklama=False)}
</section>
<section class="bl kap bl-cizgi">
<h2>Duraklar</h2>
{duraklar_html}
</section>
<section class="bl kap bl-cizgi">
<h2>Yaklaşık maliyet</h2>
<div class="yazi"><table>
<thead><tr><th>Kalem</th><th>Tutar</th><th>Nasıl hesaplandı</th></tr></thead>
<tbody>
<tr><td>Yakıt</td><td>{_tl(ozet_v["yakit"])}</td>
<td>{ozet_v["toplam_km"]} km × {YAKIT_TUKETIM} L/100 km × {int(YAKIT_FIYAT)} TL</td></tr>
<tr><td>Yeme-içme ve giriş</td><td>{_tl(ozet_v["harcama"])}</td>
<td>{KISI} kişi × {ozet_v["gece"]} gün × {GUNLUK_HARCAMA} TL <em>(varsayım)</em></td></tr>
<tr><td>Konaklama</td><td>{_tl(ozet_v["konaklama"]) if ozet_v["konaklama"] else "—"}</td>
<td>{f'fiyatını yayımlamış {ozet_v["fiyatli_durak"]} durak' if ozet_v["konaklama"] else "hiçbir durak fiyatını yayımlamamış"}</td></tr>
<tr><td><strong>Toplam</strong></td><td><strong>{_tl(ozet_v["toplam"])}</strong></td>
<td>iki kişilik tahmin</td></tr>
</tbody></table></div>
<p style="color:var(--soluk);font-size:.9rem;margin-top:12px">Yakıt ve
yeme-içme kalemleri <strong>varsayımdır</strong>; kendi rakamlarınızla
hesaplamak için <a href="/araclar/tatil-butcesi/">tatil bütçesi aracını</a>
kullanın. Konaklamaya yalnızca tesisin kendi yayımladığı fiyatlar girer,
tahmini tutar eklenmez.</p>
</section>
<section class="bl kap bl-cizgi">
<h2>Sık sorulan sorular</h2>{sss_html(sss)}</section>"""

    kirintilar = [("/", "Ana sayfa"), ("/rota/", "Rotalar"), (yol, ad)]
    ld = {
        "@context": "https://schema.org",
        "@type": "TouristTrip",
        "name": ad,
        "url": SITE + yol,
        "description": f"{len(rota)} duraklı, {ozet_v['toplam_km']} km rota; "
                       f"her durakta bir kamu misafirhanesinde konaklama.",
        "touristType": "Kamu personeli ve aileleri",
        "itinerary": {
            "@type": "ItemList",
            "numberOfItems": len(rota),
            "itemListElement": [
                {
                    "@type": "ListItem", "position": i,
                    "item": {
                        "@type": "TouristDestination",
                        "name": kisa_ad(d["tesis"]["ad"]),
                        "url": f'{SITE}/tesis/{d["slug"]}/',
                        "geo": {"@type": "GeoCoordinates",
                                "latitude": d["nokta"][0], "longitude": d["nokta"][1]},
                    },
                }
                for i, d in enumerate(rota, 1)
            ],
        },
    }
    # Uzun il zinciri basligi 70 karakteri asiyordu; baslikta ilk ve son il
    # yeter, tam zincir zaten H1'de ve gövdede duruyor.
    kisa_baslik = (f"{iller[0]}–{iller[-1]} Rotası: {len(rota)} durak, "
                   f"{ozet_v['toplam_km']} km") if len(iller) > 1 else (
                   f"{iller[0]} Rotası: {len(rota)} durak, {ozet_v['toplam_km']} km")
    return kabuk(
        baslik=kisa_baslik,
        aciklama=(f"{' – '.join(iller[:3])} arasında {len(rota)} duraklı rota: "
                  f"her durakta kamu misafirhanesi, gezilecek yerler, yöresel "
                  f"yemekler ve yaklaşık {_tl(ozet_v['toplam'])} maliyet.")[:158],
        yol=yol,
        icerik=icerik,
        kirintilar=kirintilar,
        aktif="/rota/",
        harita=True,
        jsonld=[ld, sss_ld(sss), kirinti_ld(kirintilar)],
    )


def rota_dizini(rotalar: list[list[dict]]) -> str:
    """/rota/ kök sayfası."""
    from uret import kirinti_ld, sss_html, sss_ld

    kirintilar = [("/", "Ana sayfa"), ("/rota/", "Rotalar")]
    ozetler = [(r, rota_ozeti(r)) for r in rotalar]
    ozetler.sort(key=lambda x: x[1]["toplam_km"])
    toplam_durak = sum(len(r) for r, _ in ozetler)

    kartlar = ""
    for r, o in ozetler:
        iller = []
        for d in r:
            if d["tesis"]["il"] not in iller:
                iller.append(d["tesis"]["il"])
        kartlar += f"""<a class="rota-k" href="/rota/{rota_slug(r)}/">
<strong>{e(rota_adi(r))}</strong>
<span class="rota-k-ol">{o["toplam_km"]} km · {o["gece"]} gece · {o["toplam_sure"]} sürüş</span>
<em>{e(", ".join(kisa_ad(d["tesis"]["ad"]) for d in r[:3]))}{"…" if len(r) > 3 else ""}</em>
<span class="rota-k-tl">yaklaşık {_tl(o["toplam"])}</span></a>"""

    sss = [
        ("Bu rotalar nasıl hazırlandı?",
         "Rotalar elle yazılmadı; koordinatı doğrulanmış tesisler arasından, iki "
         "durak arası bir günlük sürüşe sığacak biçimde (70–220 km) zincirlendi. "
         "Her durağın çevresinde Vikipedi'de kaydı bulunan en az üç gezilecek yer "
         "olması şart koşuldu."),
        ("Maliyetler kesin mi?",
         "Hayır. Yakıt ve yeme-içme kalemleri açıkça belirtilen varsayımlarla "
         "hesaplanır. Konaklamaya yalnızca tesisin kendi yayımladığı fiyat girer; "
         "yayımlanmamışsa tahmini tutar eklenmez."),
    ]

    icerik = f"""<section class="bl kap">
<div class="bl-bas"><div><h1>Kamu misafirhanesiyle rotalar</h1>
<p>Her durağında bir kamu misafirhanesinde kalarak yapabileceğiniz
<strong>{len(ozetler)} çok duraklı rota</strong>, toplam {toplam_durak} durak.
Her rotada haritalı güzergâh, o durakta gezilecek yerler, ilin yöresel
yemekleri ve yaklaşık maliyet var.</p></div></div>
<div class="rota-iz" style="margin-top:24px">{kartlar}</div>
</section>
<section class="bl kap bl-cizgi">
<h2>Sık sorulan sorular</h2>{sss_html(sss)}</section>"""

    ld = {
        "@context": "https://schema.org",
        "@type": "ItemList",
        "name": "Kamu misafirhanesiyle yapılabilecek rotalar",
        "numberOfItems": len(ozetler),
        "itemListElement": [
            {"@type": "ListItem", "position": i, "name": rota_adi(r),
             "url": f"{SITE}/rota/{rota_slug(r)}/"}
            for i, (r, _) in enumerate(ozetler, 1)
        ],
    }
    return kabuk(
        baslik=f"Kamu Misafirhanesiyle {len(ozetler)} Rota — harita, gezi ve maliyet",
        aciklama=f"Her durağında kamu misafirhanesinde kalarak yapabileceğiniz "
                 f"{len(ozetler)} rota: haritalı güzergâh, gezilecek yerler, "
                 f"yöresel yemekler ve yaklaşık maliyet.",
        yol="/rota/",
        icerik=icerik,
        kirintilar=kirintilar,
        aktif="/rota/",
        jsonld=[ld, sss_ld(sss), kirinti_ld(kirintilar)],
    )
