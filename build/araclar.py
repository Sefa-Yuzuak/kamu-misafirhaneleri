"""Hesaplama araçları ve "en iyi" liste sayfaları.

İki iş birden yapıyorlar:
  - Ziyaretçi için: karar verdiren somut sayı (kaç km, kaç TL, hangisi daha yakın).
  - Arama için: bu sayılar sayfada metin olarak da yazılı olduğundan hem Google
    hem de üretken arama motorları alıntılayabiliyor.

Hesaplar tarayıcıda çalışır ama her sayfa, JavaScript kapalıyken bile anlamlı
bir tablo ve açıklama gösterir — boş bir araç kabuğu asla yayımlanmaz.
"""

from __future__ import annotations

from parca import AD, SITE, e, ik, kabuk
from mesafe import CIKIS_NOKTALARI, ORT_HIZ, SAPMA, karayolu_km, sure_metni, sure_saat
from veri import TURLER, kisa_ad, slug, tesis_slug

# --------------------------------------------------------------------------
# Ortak parçalar
# --------------------------------------------------------------------------

ARACLAR = [
    ("en-yakin", "Bana en yakın kamu tesisi", "konum",
     "Bulunduğunuz ile göre en yakın tesisleri mesafe sırasıyla listeler."),
    ("tatil-butcesi", "Tatil bütçesi hesaplayıcı", "para",
     "Konaklama, yakıt ve yol masrafını birlikte hesaplar; otelle karşılaştırır."),
    ("mesafe", "Mesafe ve süre hesaplayıcı", "yol",
     "İki nokta arası tahmini karayolu mesafesi ve sürüş süresi."),
    ("karsilastir", "Tesis karşılaştırma", "harita",
     "Üç tesisi yan yana koyup fiyat, olanak ve mesafeyi karşılaştırır."),
]

_TAHMIN_NOTU = (
    f"Mesafeler kuş uçuşu uzaklığın {str(SAPMA).replace('.', ',')} katsayısıyla "
    "çarpılmasıyla tahmin edilir; ölçülmüş karayolu mesafesi değildir. Bilinen "
    "güzergâhlarda sapma ortalama %6'dır. Süre saatte "
    f"{int(ORT_HIZ)} km ortalama hızla, mola hariç hesaplanır."
)


def _arac_kabugu(anahtar: str, baslik: str, ikon: str, ozet: str, govde: str,
                 sss: list[tuple[str, str]], aciklama: str,
                 ek_ld: list[dict] | None = None) -> str:
    from uret import kirinti_ld, sss_html, sss_ld

    yol = f"/araclar/{anahtar}/"
    kirintilar = [("/", "Ana sayfa"), ("/araclar/", "Araçlar"), (yol, baslik)]
    digerleri = "".join(
        f'<a class="dg dg-2 dg-sm" href="/araclar/{a}/">{ik(i)}{e(b)}</a>'
        for a, b, i, _ in ARACLAR
        if a != anahtar
    )
    icerik = f"""<section class="bl kap" style="max-width:900px">
<span class="rz rz-vurgu">{ik(ikon)}Hesaplama aracı</span>
<h1 style="margin-top:10px">{e(baslik)}</h1>
<p class="ozet" style="margin-top:18px">{ozet}</p>
{govde}
<div class="not" style="margin-top:22px">{ik("uyari")}<div>{e(_TAHMIN_NOTU)}</div></div>
</section>
<section class="bl kap bl-cizgi" style="max-width:900px">
<h2>Sık sorulan sorular</h2>{sss_html(sss)}</section>
<section class="bl kap bl-cizgi" style="max-width:900px">
<h2>Diğer araçlar</h2>
<div style="display:flex;flex-wrap:wrap;gap:9px;margin-top:14px">{digerleri}</div>
</section>"""
    return kabuk(
        baslik=f"{baslik} — kamu misafirhaneleri",
        aciklama=aciklama[:158],
        yol=yol,
        icerik=icerik,
        kirintilar=kirintilar,
        aktif="/araclar/",
        arac=True,
        jsonld=[
            {
                "@context": "https://schema.org",
                "@type": "WebApplication",
                "name": baslik,
                "url": SITE + yol,
                "applicationCategory": "TravelApplication",
                "operatingSystem": "Web",
                "inLanguage": "tr-TR",
                "isAccessibleForFree": True,
                "offers": {"@type": "Offer", "price": "0", "priceCurrency": "TRY"},
            },
            sss_ld(sss),
            kirinti_ld(kirintilar),
            *(ek_ld or []),
        ],
    )


def _il_secenekleri(il_merkez: dict) -> str:
    return "".join(f'<option value="{e(i)}">{e(i)}</option>' for i in sorted(il_merkez))


# --------------------------------------------------------------------------
# 1) Bana en yakın kamu tesisi
# --------------------------------------------------------------------------


def en_yakin_sayfasi(tesisler: list[dict], konumlar: dict, il_merkez: dict) -> str:
    konumlu = [t for t in tesisler if konumlar.get(tesis_slug(t))]

    # JavaScript kapalıyken de işe yarasın: Ankara'dan en yakın 15 tesis yazılı gelir
    ank = next(((la, lo) for ad, la, lo in CIKIS_NOKTALARI if ad == "Ankara"))
    hazir = sorted(
        ((t, karayolu_km(ank, (konumlar[tesis_slug(t)]["lat"],
                               konumlar[tesis_slug(t)]["lon"]))) for t in konumlu),
        key=lambda x: x[1],
    )[:15]
    hazir_satir = "".join(
        f'<tr><td><strong>{km} km</strong></td>'
        f'<td><a href="/tesis/{tesis_slug(t)}/">{e(kisa_ad(t["ad"]))}</a></td>'
        f'<td>{e(t["ilce"])}, {e(t["il"])}</td>'
        f'<td>{e(sure_metni(sure_saat(km)))}</td></tr>'
        for t, km in hazir
    )

    ozet = (
        f"Bu araç, seçtiğiniz ilden <strong>{len(konumlu)} kamu tesisinin</strong> "
        "hepsine olan tahmini karayolu mesafesini hesaplar ve en yakından başlayarak "
        "sıralar. Tür, denize yakınlık ve havuz gibi süzgeçlerle daraltabilirsiniz. "
        "Hesap tarayıcınızda yapılır, hiçbir konum bilgisi sunucuya gönderilmez."
    )

    govde = f"""
<div class="arac">
<div class="arac-satir">
<label class="alan"><span>Nereden yola çıkıyorsunuz?</span>
<select id="a-il">{_il_secenekleri(il_merkez)}</select></label>
<label class="alan"><span>Tesis türü</span>
<select id="a-tur"><option value="">Hepsi</option>
{"".join(f'<option value="{e(k)}">{e(v[0])}</option>' for k, v in TURLER.items())}
</select></label>
<label class="alan"><span>Kaç tesis listelensin?</span>
<select id="a-adet"><option>15</option><option selected>25</option><option>50</option></select></label>
</div>
<div class="arac-satir arac-onay">
<label class="onay"><input type="checkbox" id="a-deniz"><span>{ik("deniz")}Denize yakın olsun</span></label>
<label class="onay"><input type="checkbox" id="a-havuz"><span>{ik("havuz")}Havuzu olsun</span></label>
<label class="onay"><input type="checkbox" id="a-fiyat"><span>{ik("para")}Fiyatı yayımlanmış olsun</span></label>
</div>
</div>
<p id="a-ozet" class="arac-ozet" role="status"></p>
<div id="a-sonuc" class="arac-sonuc"></div>

<noscript><p class="not">{ik("bilgi")} Hesaplayıcı JavaScript gerektirir.
Aşağıda Ankara'dan en yakın 15 tesis hazır listelenmiştir.</p></noscript>

<h2 style="margin-top:34px">Ankara'ya en yakın 15 kamu tesisi</h2>
<p style="color:var(--soluk);font-size:.94rem">Aracı kullanamıyorsanız bu hazır liste
işinizi görür. Ankara dışından geliyorsanız yukarıdan ilinizi seçin.</p>
<div class="yazi"><table><thead><tr><th>Mesafe</th><th>Tesis</th><th>Konum</th>
<th>Süre</th></tr></thead><tbody>{hazir_satir}</tbody></table></div>"""

    sss = [
        ("Bana en yakın öğretmenevi hangisi?",
         f"İlinizi seçtiğinizde bu araç {len(konumlu)} tesisin tamamına olan tahmini "
         "mesafeyi hesaplayıp en yakından başlayarak sıralar. Ankara'dan çıkanlar için "
         f"en yakını {kisa_ad(hazir[0][0]['ad'])} ({hazir[0][1]} km), ardından "
         f"{kisa_ad(hazir[1][0]['ad'])} ({hazir[1][1]} km) geliyor."),
        ("Mesafeler ne kadar güvenilir?",
         _TAHMIN_NOTU + " Yola çıkmadan önce bir harita uygulamasından teyit edin."),
        ("Konumum kaydediliyor mu?",
         "Hayır. Seçtiğiniz il tarayıcınızdan çıkmaz; hesap tamamen cihazınızda "
         "yapılır ve sunucuya hiçbir konum bilgisi gönderilmez."),
    ]
    return _arac_kabugu(
        "en-yakin", "Bana en yakın kamu tesisi", "konum", ozet, govde, sss,
        f"Bulunduğunuz ile göre en yakın öğretmenevi, polisevi ve kamu misafirhanesini "
        f"mesafe sırasıyla bulun. {len(konumlu)} tesis, tahmini karayolu mesafesiyle.",
    )


# --------------------------------------------------------------------------
# 2) Tatil bütçesi
# --------------------------------------------------------------------------


def butce_sayfasi(tesisler: list[dict], konumlar: dict, il_merkez: dict) -> str:
    fiyatli = [t for t in tesisler if t.get("fiyat_2026")]
    ozet = (
        "Bir kamu tesisinde tatilin gerçek maliyeti yalnızca oda ücreti değildir; "
        "yol ve yemek çoğu zaman konaklamayı geçer. Bu araç üçünü birlikte hesaplar "
        "ve aynı tatilin ticari bir otelde ne tutacağıyla karşılaştırır. "
        f"Yayımlanmış fiyatı bilinen {len(fiyatli)} tesis seçildiğinde oda ücreti "
        "kendiliğinden dolar; diğerlerinde kendi aldığınız fiyatı yazarsınız."
    )

    govde = f"""
<div class="arac">
<div class="arac-satir">
<label class="alan"><span>Nereden</span>
<select id="b-il">{_il_secenekleri(il_merkez)}</select></label>
<label class="alan alan-genis"><span>Hangi tesis</span>
<input type="search" id="b-tesis" placeholder="Tesis adı yazın — örn. Ayvalık"
autocomplete="off" role="combobox" aria-expanded="false" aria-controls="b-oneri">
<div class="oneri oneri-alan" id="b-oneri" role="listbox"></div></label>
</div>
<div class="arac-satir">
<label class="alan"><span>Gece sayısı</span>
<input type="number" id="b-gece" value="4" min="1" max="30" inputmode="numeric"></label>
<label class="alan"><span>Yetişkin</span>
<input type="number" id="b-yetiskin" value="2" min="1" max="10" inputmode="numeric"></label>
<label class="alan"><span>Çocuk</span>
<input type="number" id="b-cocuk" value="1" min="0" max="10" inputmode="numeric"></label>
</div>
<div class="arac-satir">
<label class="alan"><span>Oda ücreti (gecelik, TL)</span>
<input type="number" id="b-oda" value="2500" min="0" step="50" inputmode="numeric">
<small id="b-oda-not"></small></label>
<label class="alan"><span>Yakıt (L/100 km)</span>
<input type="number" id="b-tuketim" value="7" min="1" max="30" step="0.5" inputmode="decimal"></label>
<label class="alan"><span>Yakıt fiyatı (TL/L)</span>
<input type="number" id="b-yakit" value="50" min="1" step="0.5" inputmode="decimal">
<small>Güncel fiyatı siz girin</small></label>
</div>
<div class="arac-satir">
<label class="alan"><span>Kişi başı günlük harcama (TL)</span>
<input type="number" id="b-harcama" value="600" min="0" step="50" inputmode="numeric">
<small>Yemek, gezi, giriş ücretleri</small></label>
<label class="alan"><span>Karşılaştırma: otel gecelik (TL)</span>
<input type="number" id="b-otel" value="6000" min="0" step="250" inputmode="numeric">
<small>Aynı tarihte bir otel ne isterdi?</small></label>
</div>
</div>
<div id="b-sonuc" class="hesap-sonuc" role="status"></div>
<noscript><p class="not">{ik("bilgi")} Hesaplayıcı JavaScript gerektirir.</p></noscript>

<h2 style="margin-top:32px">Hesap nasıl yapılıyor?</h2>
<div class="yazi">
<ul>
<li><strong>Konaklama</strong> = gecelik oda ücreti × gece sayısı. Kamu tesislerinde
fiyat çoğunlukla oda başınadır, kişi başı değil; üç–dört kişilik odalarda ayrı
tarife uygulanır.</li>
<li><strong>Yakıt</strong> = tahmini mesafe × 2 (gidiş-dönüş) × tüketim ÷ 100 × litre fiyatı.</li>
<li><strong>Harcama</strong> = kişi başı günlük tutar × kişi sayısı × (gece + 1) gün.</li>
<li><strong>Otel karşılaştırması</strong> yalnızca konaklama farkını gösterir; yol ve
yemek her iki durumda da aynı olduğu için tasarrufa dahil edilmez.</li>
</ul>
<p>Köprü, otoyol ve otopark ücretleri hesaba katılmaz. Sonuç bir tahmindir,
bağlayıcı bir fiyat teklifi değildir.</p>
</div>"""

    sss = [
        ("Kamu misafirhanesinde tatil ne kadara mal olur?",
         "Yayımlanmış tarifelere göre iki kişilik oda çoğunlukla 1.500–3.000 TL, "
         "üç–dört kişilik oda 2.500–4.500 TL bandında. Dört gecelik bir tatilde "
         "konaklama 6.000–18.000 TL arasında değişiyor; buna yol ve yemek eklenir. "
         "Kendi rakamlarınızla hesaplamak için yukarıdaki aracı kullanın."),
        ("Kamu tesisi otelden ne kadar ucuz?",
         "Yayımlanmış kamu tarifeleri, aynı bölgedeki ticari otellerin sezon "
         "fiyatlarının genellikle üçte biri ile yarısı arasında kalıyor. Kesin fark "
         "tesise, sezona ve kurum personeli olup olmadığınıza göre değişir; araç "
         "kendi girdiğiniz otel fiyatıyla farkı hesaplar."),
        ("Çocuklar için ayrı ücret alınıyor mu?",
         "Kamu tesislerinde fiyat genellikle oda başınadır. Üç–dört kişilik odalar "
         "için ayrı tarife vardır; küçük çocuklar için indirim uygulaması tesise "
         "göre değişir, rezervasyon sırasında sorulmalıdır."),
    ]
    return _arac_kabugu(
        "tatil-butcesi", "Tatil bütçesi hesaplayıcı", "para", ozet, govde, sss,
        "Kamu misafirhanesinde tatilin gerçek maliyetini hesaplayın: konaklama, "
        "yakıt ve günlük harcama bir arada, otelle karşılaştırmalı.",
    )


# --------------------------------------------------------------------------
# 3) Mesafe ve süre
# --------------------------------------------------------------------------


def mesafe_sayfasi(tesisler: list[dict], konumlar: dict, il_merkez: dict) -> str:
    # yazılı tablo: üç büyük çıkıştan il merkezlerine
    iller = sorted(il_merkez)
    satirlar = ""
    for il in iller:
        h = il_merkez[il]
        hucreler = "".join(
            f"<td>{karayolu_km((la, lo), h)} km</td>" for _, la, lo in CIKIS_NOKTALARI
        )
        satirlar += (
            f'<tr><td><a href="/il/{slug(il)}/">{e(il)}</a></td>{hucreler}</tr>'
        )
    baslik_hucre = "".join(f"<th>{e(a)}</th>" for a, _, _ in CIKIS_NOKTALARI)

    ozet = (
        "Bir kamu tesisine yola çıkmadan önceki ilk soru mesafedir. Bu araç "
        f"{len(konumlar)} tesisin koordinatını kullanarak seçtiğiniz ilden tesise "
        "tahmini karayolu mesafesini, sürüş süresini ve yakıt maliyetini verir. "
        "Aşağıdaki tablo ise 81 ilin Ankara, İstanbul ve İzmir'e uzaklığını hazır "
        "olarak listeler."
    )

    govde = f"""
<div class="arac">
<div class="arac-satir">
<label class="alan"><span>Nereden</span>
<select id="m-il">{_il_secenekleri(il_merkez)}</select></label>
<label class="alan alan-genis"><span>Nereye (tesis)</span>
<input type="search" id="m-tesis" placeholder="Tesis adı yazın" autocomplete="off"
role="combobox" aria-expanded="false" aria-controls="m-oneri">
<div class="oneri oneri-alan" id="m-oneri" role="listbox"></div></label>
</div>
<div class="arac-satir">
<label class="alan"><span>Yakıt (L/100 km)</span>
<input type="number" id="m-tuketim" value="7" min="1" max="30" step="0.5" inputmode="decimal"></label>
<label class="alan"><span>Yakıt fiyatı (TL/L)</span>
<input type="number" id="m-yakit" value="50" min="1" step="0.5" inputmode="decimal"></label>
</div>
</div>
<div id="m-sonuc" class="hesap-sonuc" role="status"></div>

<h2 style="margin-top:32px">81 ilin üç büyük şehre uzaklığı</h2>
<p style="color:var(--soluk);font-size:.94rem">Tahmini karayolu mesafesi, kilometre.</p>
<div class="yazi"><table><thead><tr><th>İl</th>{baslik_hucre}</tr></thead>
<tbody>{satirlar}</tbody></table></div>"""

    sss = [
        ("Ankara'dan denize kaç saat sürer?",
         "Ankara'ya en yakın kıyı tesisleri yaklaşık 4,5–5 saat mesafede (Karadeniz "
         "kıyısı). Ege ve Akdeniz kıyısındaki tesisler 6–8 saat arasında değişir. "
         "Tesise özel süre için yukarıdaki aracı kullanın."),
        ("Mesafeler ölçülmüş mü?",
         _TAHMIN_NOTU),
        ("Yakıt maliyeti nasıl hesaplanıyor?",
         "Gidiş-dönüş mesafe × aracınızın 100 km'de yaktığı litre ÷ 100 × girdiğiniz "
         "litre fiyatı. Köprü ve otoyol ücretleri dahil değildir."),
    ]
    return _arac_kabugu(
        "mesafe", "Mesafe ve süre hesaplayıcı", "yol", ozet, govde, sss,
        "İlinizden kamu misafirhanesine tahmini karayolu mesafesi, sürüş süresi ve "
        "yakıt maliyeti. 81 ilin Ankara, İstanbul ve İzmir'e uzaklık tablosu.",
    )


# --------------------------------------------------------------------------
# 4) Karşılaştırma
# --------------------------------------------------------------------------


def karsilastir_sayfasi(tesisler: list[dict]) -> str:
    ozet = (
        "İki veya üç tesisi yan yana koyun: tür, konum, yayımlanmış fiyat, denize "
        "konumu, olanaklar ve seçtiğiniz ilden mesafe aynı tabloda görünsün. "
        "Özellikle aynı bölgede birkaç tesis arasında karar verirken işe yarar."
    )
    govde = f"""
<div class="arac">
<div class="arac-satir">
<label class="alan alan-genis"><span>1. tesis</span>
<input type="search" id="k-1" placeholder="Tesis adı yazın" autocomplete="off"
role="combobox" aria-expanded="false" aria-controls="k-1-oneri">
<div class="oneri oneri-alan" id="k-1-oneri" role="listbox"></div></label>
<label class="alan alan-genis"><span>2. tesis</span>
<input type="search" id="k-2" placeholder="Tesis adı yazın" autocomplete="off"
role="combobox" aria-expanded="false" aria-controls="k-2-oneri">
<div class="oneri oneri-alan" id="k-2-oneri" role="listbox"></div></label>
<label class="alan alan-genis"><span>3. tesis (isteğe bağlı)</span>
<input type="search" id="k-3" placeholder="Tesis adı yazın" autocomplete="off"
role="combobox" aria-expanded="false" aria-controls="k-3-oneri">
<div class="oneri oneri-alan" id="k-3-oneri" role="listbox"></div></label>
</div>
</div>
<div id="k-sonuc" class="karsilastir-sonuc"></div>
<noscript><p class="not">{ik("bilgi")} Karşılaştırma JavaScript gerektirir.
Tesisleri tek tek incelemek için <a href="/il/">il listesini</a> kullanabilirsiniz.</p></noscript>"""

    sss = [
        ("Hangi kamu tesisi daha iyi?",
         "Tek bir doğru cevap yok; karar genellikle üç şeye bakar: yola ne kadar "
         "dayanabileceğiniz, denize/havuza ihtiyacınız ve bütçe. Bu araç seçtiğiniz "
         "tesisleri bu üç başlıkta yan yana koyar."),
        ("Karşılaştırmada fiyat neden bazı tesislerde boş?",
         "Bu sitede fiyat yalnızca tesis kendisi yayımlamışsa yazılır. Tahmini "
         "rakam verilmediği için yayımlanmamış tesislerde alan boş kalır; fiyat "
         "telefonla öğrenilmelidir."),
    ]
    return _arac_kabugu(
        "karsilastir", "Tesis karşılaştırma", "harita", ozet, govde, sss,
        "İki veya üç kamu misafirhanesini fiyat, olanak, denize konum ve mesafe "
        "açısından yan yana karşılaştırın.",
    )


# --------------------------------------------------------------------------
# Araç dizini
# --------------------------------------------------------------------------


def araclar_dizini(tesisler: list[dict], konumlar: dict) -> str:
    from uret import kirinti_ld

    kirintilar = [("/", "Ana sayfa"), ("/araclar/", "Araçlar")]
    kartlar = "".join(
        f"""<a class="tur-k" href="/araclar/{a}/">{ik(i, "ik tur-ik")}
<strong>{e(b)}</strong><em>{e(ac)}</em>
<span class="tur-ok">{ik("ok")}</span></a>"""
        for a, b, i, ac in ARACLAR
    )
    icerik = f"""<section class="bl kap">
<div class="bl-bas"><div><h1>Hesaplama araçları</h1>
<p>{len(konumlar)} tesisin koordinatı ve yayımlanmış fiyatları üzerinden çalışan
dört araç. Hepsi tarayıcınızda hesaplar; hiçbir bilgi sunucuya gönderilmez.</p>
</div></div>
<div class="tur-iz">{kartlar}</div>
</section>"""
    return kabuk(
        baslik="Hesaplama araçları — mesafe, bütçe ve karşılaştırma",
        aciklama="Kamu misafirhaneleri için mesafe, yakıt maliyeti, tatil bütçesi ve "
        "tesis karşılaştırma araçları. Ücretsiz, kayıt gerektirmez.",
        yol="/araclar/",
        icerik=icerik,
        kirintilar=kirintilar,
        aktif="/araclar/",
        jsonld=[kirinti_ld(kirintilar)],
    )
