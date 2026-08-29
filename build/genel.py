"""Liste sayfaları, rehber yazıları ve tüm sitenin derlenmesi. Giriş noktası budur."""

from __future__ import annotations

import json
import shutil
import sys
from collections import defaultdict
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from parca import AD, SITE, e, ik, il_karti, kabuk, tesis_karti  # noqa: E402
from uret import (  # noqa: E402
    CIKTI,
    KOK,
    il_sayfasi,
    kirinti_ld,
    kurum_tam,
    sss_html,
    sss_ld,
    tesis_sayfasi,
)
from veri import TURLER, slug, tesis_slug, tur_slug  # noqa: E402

BUGUN = date.today()
AY_TR = "Ocak Şubat Mart Nisan Mayıs Haziran Temmuz Ağustos Eylül Ekim Kasım Aralık".split()
TARIH_TR = f"{BUGUN.day} {AY_TR[BUGUN.month - 1]} {BUGUN.year}"


def yaz(yol: str, icerik: str) -> None:
    p = CIKTI / yol.strip("/")
    if not p.suffix:
        p = p / "index.html"
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(icerik, "utf-8")


# --------------------------------------------------------------------------
# Ana sayfa
# --------------------------------------------------------------------------


def ana_sayfa(tesisler: list[dict], gorseller: dict, kurumlar: dict) -> str:
    il_grup = defaultdict(list)
    for t in tesisler:
        il_grup[t["il"]].append(t)
    deniz = [t for t in tesisler if t.get("deniz")]
    fiyatli = [t for t in tesisler if t.get("fiyat_2026")]
    telefonlu = [t for t in tesisler if t.get("telefon")]

    kiyi_iller = sorted(
        [(il, ts) for il, ts in il_grup.items() if any(t.get("kiyi") for t in ts)],
        key=lambda x: -sum(1 for t in x[1] if t.get("deniz")),
    )[:8]

    il_kartlari = "".join(
        il_karti(il, len(ts), sum(1 for t in ts if t.get("deniz")), gorseller)
        for il, ts in sorted(il_grup.items())
    )
    kiyi_kartlari = "".join(
        il_karti(il, len(ts), sum(1 for t in ts if t.get("deniz")), gorseller)
        for il, ts in kiyi_iller
    )

    tur_kartlari = ""
    for tur, (cogul, kisa, ikon, aciklama) in TURLER.items():
        adet = sum(1 for t in tesisler if t["tur"] == tur)
        tur_kartlari += f"""<a class="tur-k" href="/tur/{tur_slug(tur)}/">
{ik(ikon, "ik tur-ik")}<strong>{e(cogul)}</strong>
<span>{adet} tesis</span><em>{e(aciklama)}</em>
<span class="tur-ok">{ik("ok")}</span></a>"""

    logolar = "".join(
        f'<a class="logo-h" href="{e(v["site"])}" target="_blank" rel="noopener nofollow" '
        f'title="{e(v["ad"])}"><img src="/img/kurum/{v["dosya"]}" width="256" height="256" '
        f'loading="lazy" decoding="async" alt="{e(v["ad"])} amblemi"></a>'
        for v in kurumlar.values()
        if v.get("dosya")
    )

    one_cikan = sorted(
        [t for t in tesisler if t.get("deniz") and t.get("fiyat_2026")],
        key=lambda t: t.get("ankara_saat") or 99,
    )[:6]
    if len(one_cikan) < 6:
        one_cikan += [t for t in deniz if t not in one_cikan][: 6 - len(one_cikan)]

    icerik = f"""<section class="kahraman"><div class="kap">
<h1>Türkiye'nin kamu misafirhaneleri, <em>tek yerde</em>.</h1>
<p class="giris">81 ilde {len(tesisler)} öğretmenevi, polisevi, üniversite ve bakanlık
tesisi. Telefon numarası, yayımlanmış fiyatlar ve yol tarifi — reklamsız, ücretsiz.</p>
<div class="ara">
<svg class="ik ik-ara" viewBox="0 0 24 24" aria-hidden="true"><path d="M17.5 17.5 21 21M19.5 11.2a8.2 8.2 0 1 1-16.5 0 8.2 8.2 0 0 1 16.5 0Z"/></svg>
<input type="search" id="q" placeholder="Tesis, ilçe veya il ara — örn. Ayvalık" autocomplete="off"
role="combobox" aria-expanded="false" aria-controls="oneri" aria-label="Tesis ara">
<kbd>/</kbd>
<div class="oneri" id="oneri" role="listbox"></div>
</div>
<ul class="sayilar">
<li><b>{len(tesisler)}</b> tesis</li>
<li><b>81</b> il</li>
<li><b>{len(telefonlu)}</b> telefon numarası</li>
<li><b>{len(deniz)}</b> denize yakın</li>
<li><b>{len(fiyatli)}</b> yayımlanmış fiyat listesi</li>
</ul>
</div></section>

<section class="bl kap">
<div class="bl-bas"><div><h2>Tesis türleri</h2>
<p>Her tür farklı bir kuruma bağlıdır; kimlerin kalabildiği ve fiyatlandırma buna göre değişir.</p>
</div></div>
<div class="tur-iz">{tur_kartlari}</div>
</section>

<section class="bl kap bl-cizgi">
<div class="bl-bas"><div><h2>Deniz tatili için</h2>
<p>Konumu doğrulanmış, denize yakın {len(deniz)} tesis arasından öne çıkanlar.</p></div>
<a class="dg dg-2 dg-sm" href="/deniz/">Tümünü gör{ik("ok")}</a></div>
<div class="iz">{"".join(tesis_karti(t, gorseller) for t in one_cikan)}</div>
</section>

<section class="bl kap bl-cizgi">
<div class="bl-bas"><div><h2>Kıyı illeri</h2>
<p>Denize komşu illerdeki kamu tesisleri.</p></div>
<a class="dg dg-2 dg-sm" href="/il/">81 ilin tamamı{ik("ok")}</a></div>
<div class="iz-il">{kiyi_kartlari}</div>
</section>

<section class="bl kap bl-cizgi">
<div class="bl-bas"><div><h2>Bilmeniz gerekenler</h2>
<p>Kimler kalabilir, fiyatlar ne kadar, rezervasyon nasıl yapılır.</p></div></div>
<div class="iz">{rehber_kartlari()}</div>
</section>

<section class="bl kap bl-cizgi">
<div class="bl-bas"><div><h2>Tüm iller</h2>
<p>81 ilin tamamı, tesis sayılarıyla.</p></div></div>
<div class="iz-il">{il_kartlari}</div>
</section>

<section class="bl kap bl-cizgi">
<div class="bl-bas"><div><h2>Veriler bu kurumlardan</h2>
<p>Tesis bilgileri kurumların kendi resmî yayınlarından derlendi. Logolar ilgili
kurumlara aittir; kaynağı göstermek için kullanılmaktadır.</p></div>
<a class="dg dg-2 dg-sm" href="/kaynaklar/">Kaynaklar{ik("ok")}</a></div>
<div class="logo-duvar">{logolar}</div>
</section>"""

    ld = [
        {
            "@context": "https://schema.org",
            "@type": "WebSite",
            "@id": SITE + "/#site",
            "name": AD,
            "url": SITE + "/",
            "inLanguage": "tr-TR",
            "description": (
                f"Türkiye'nin 81 ilindeki {len(tesisler)} kamu konaklama tesisinin "
                "bağımsız dizini."
            ),
            "potentialAction": {
                "@type": "SearchAction",
                "target": {
                    "@type": "EntryPoint",
                    "urlTemplate": SITE + "/ara/?q={search_term_string}",
                },
                "query-input": "required name=search_term_string",
            },
        },
        {
            "@context": "https://schema.org",
            "@type": "CollectionPage",
            "name": AD,
            "url": SITE + "/",
            "dateModified": BUGUN.isoformat(),
            "about": [{"@type": "Thing", "name": t} for t in TURLER],
        },
    ]

    return kabuk(
        baslik=f"{AD} — 81 ilde {len(tesisler)} öğretmenevi, polisevi ve kamu tesisi",
        aciklama=(
            f"Türkiye'nin 81 ilindeki {len(tesisler)} kamu misafirhanesi: telefon numaraları, "
            f"2026 fiyatları, denize yakın {len(deniz)} tesis. Ücretsiz, reklamsız dizin."
        ),
        yol="/",
        icerik=icerik,
        jsonld=ld,
    )


# --------------------------------------------------------------------------
# Rehber
# --------------------------------------------------------------------------

REHBERLER = [
    ("ogretmenevinde-kimler-kalabilir", "Öğretmenevinde kimler kalabilir?", "okul"),
    ("ogretmenevi-fiyatlari", "Kamu misafirhanesi fiyatları (2026)", "para"),
    ("denize-sifir-kamu-tesisleri", "Denize yakın kamu tesisleri", "deniz"),
    ("rezervasyon-nasil-yapilir", "Rezervasyon nasıl yapılır?", "telefon"),
    ("ankaraya-yakin-deniz-tatili", "Ankara'ya yakın deniz tatili", "yol"),
]

REHBER_OZET = {
    "ogretmenevinde-kimler-kalabilir": "Öğretmenevi, polisevi ve üniversite misafirhanelerinde konaklama önceliği kimde?",
    "ogretmenevi-fiyatlari": "Fiyat listesini yayımlamış tesislerin karşılaştırmalı tablosu.",
    "denize-sifir-kamu-tesisleri": "Konumu doğrulanmış, denize yakın tesislerin tam listesi.",
    "rezervasyon-nasil-yapilir": "Merkezî sistem yok; adım adım nasıl yer bulunur.",
    "ankaraya-yakin-deniz-tatili": "Ankara'dan 7,5 saatin altındaki kıyı tesisleri.",
}


def rehber_kartlari() -> str:
    p = ""
    for s, baslik, ikon in REHBERLER[:3]:
        p += f"""<article class="tk rehber-k"><div class="tk-govde" style="padding:20px 20px 0">
<span class="rz rz-vurgu">{ik(ikon)}Rehber</span>
<h3 class="tk-ad" style="margin-top:10px"><a href="/rehber/{s}/">{e(baslik)}</a></h3>
<p style="font-size:.9rem;color:var(--soluk)">{e(REHBER_OZET[s])}</p></div>
<div class="tk-alt"><span class="dg dg-3 dg-sm" style="padding:0">Oku{ik("ok")}</span></div></article>"""
    return p


def _tablo(basliklar: list[str], satirlar: list[list[str]]) -> str:
    b = "".join(f"<th>{e(x)}</th>" for x in basliklar)
    s = "".join("<tr>" + "".join(f"<td>{x}</td>" for x in r) + "</tr>" for r in satirlar)
    return f"<table><thead><tr>{b}</tr></thead><tbody>{s}</tbody></table>"


def _link(t: dict) -> str:
    return f'<a href="/tesis/{tesis_slug(t)}/">{e(t["ad"])}</a>'


def rehber_govde(anahtar: str, tesisler: list[dict]) -> tuple[str, list[tuple[str, str]]]:
    deniz = [t for t in tesisler if t.get("deniz")]
    fiyatli = [t for t in tesisler if t.get("fiyat_2026")]

    if anahtar == "ogretmenevinde-kimler-kalabilir":
        govde = f"""
<p>Türkiye'de kamu konaklama tesisleri tek bir kurala bağlı değildir. Her tesis
bağlı olduğu kurumun yönergesine göre çalışır ve <strong>öncelik sırası</strong>
tesisten tesise değişir. Bu dizindeki {len(tesisler)} tesis dört gruba ayrılıyor.</p>
{_tablo(["Tür", "Adet", "Öncelikli konuk", "Diğer kamu personeli"], [
[f'<a href="/tur/{tur_slug(k)}/">{e(v[0])}</a>',
 str(sum(1 for t in tesisler if t["tur"] == k)),
 {"Öğretmenevi": "MEB personeli ve emeklileri",
  "Polisevi": "Emniyet mensupları ve emeklileri",
  "Üniversite Misafirhanesi": "Üniversitenin kendi personeli",
  "Kamu Misafirhanesi": "Bağlı kurumun personeli"}[k],
 "Boşluk durumuna göre kabul edilir"] for k, v in TURLER.items()])}
<h2>Pratikte ne oluyor?</h2>
<p>Sezon dışında ve hafta içi çoğu tesiste yer bulunur; kamu personeli kimliğiyle
konaklama genellikle mümkündür. Yaz aylarında sahil tesislerinde öncelikli gruplar
kontenjanı doldurabilir. <strong>Fiyat da gruba göre değişir:</strong> aynı odada
MEB personeli, diğer kamu personeli ve dışarıdan gelen misafir için üç ayrı tarife
uygulanabiliyor.</p>
<blockquote>Örnek: Ayvalık Öğretmenevi'nin yayımladığı 2026 listesinde iki kişilik oda
kamu personeline 2.800 TL, MEB personeline 2.200 TL olarak duyuruldu.</blockquote>
<h2>Yanınıza almanız gerekenler</h2>
<ul>
<li><strong>Kurum kimliği</strong> — çalışan veya emekli kimliği.</li>
<li><strong>Yakınlık belgesi</strong> — eş ve çocuklar için nüfus kayıt örneği istenebilir.</li>
<li><strong>Rezervasyon teyidi</strong> — telefonda alınan kaydın adı ve tarihi.</li>
</ul>
<p>Kesin kural yoktur: gitmeden önce tesisi arayıp <em>"kamu personeliyim, eşim ve
çocuğumla kalacağım, uygun mu?"</em> diye sormak en güvenilir yöntemdir.</p>"""
        sss = [
            ("Öğretmen olmayan kamu personeli öğretmenevinde kalabilir mi?",
             "Çoğu öğretmenevinde boşluk durumuna göre kalabilir, ancak fiyat farkı "
             "uygulanabilir ve yoğun sezonda MEB personeline öncelik verilir. "
             "Uygulama tesise göre değiştiği için önceden telefonla teyit gerekir."),
            ("Emekli kamu personeli konaklayabilir mi?",
             "Genel uygulama emeklilerin de kabul edildiği yönündedir; emekli kimliği "
             "istenir. Tesisin kendi yönergesi belirleyicidir."),
            ("Eş ve çocuklar için ek ücret alınır mı?",
             "Oda tipine göre fiyatlandırma yapılır. Yayımlanmış listelerde iki kişilik "
             "ve üç–dört kişilik oda için ayrı tarifeler görülüyor; çocuk indirimi "
             "tesise göre değişir."),
        ]
        return govde, sss

    if anahtar == "ogretmenevi-fiyatlari":
        sat = sorted(fiyatli, key=lambda t: (t["il"], t["ad"]))
        govde = f"""
<p>Kamu konaklama tesislerinin <strong>merkezî bir fiyat listesi yoktur</strong>.
Her tesis kendi tarifesini belirler ve çoğu bunu internette yayımlamaz. Bu dizinde
{len(tesisler)} tesis kayıtlı; bunlardan <strong>{len(fiyatli)} tanesinin</strong>
yayımlanmış 2026 fiyatına ulaşılabildi. Aşağıdaki tablo tamamen bu kurumların kendi
duyurularından alınmıştır — tahmin veya ortalama yazılmamıştır.</p>
{_tablo(["Tesis", "İl", "Yayımlanan 2026 fiyatı"],
        [[_link(t), f'<a href="/il/{slug(t["il"])}/">{e(t["il"])}</a>', e(t["fiyat_2026"])] for t in sat])}
<h2>Tablodan çıkan tablo</h2>
<p>Yayımlanmış tarifelerde iki kişilik oda genellikle <strong>1.500–3.000 TL</strong>
bandında, üç–dört kişilik oda ise <strong>2.500–4.500 TL</strong> bandında duyurulmuş
durumda. Sahil tesisleri bandın üst ucunda, iç bölgelerdeki tesisler alt ucunda yer
alıyor. Çoğu tesiste <strong>açık büfe kahvaltı fiyata dahil</strong>.</p>
<h2>Fiyatı yayımlanmamış tesisler</h2>
<p>Kalan {len(tesisler) - len(fiyatli)} tesis için bu sitede fiyat yazılmaz. Tahmini
rakam vermek yanıltıcı olurdu; ilgili tesisin sayfasındaki telefon numarasından
güncel tarife öğrenilebilir.</p>
<div class="not">{ik("uyari")}<div>Fiyatlar kurumlar tarafından yıl içinde
güncellenebilir. Tablodaki her tesisin kendi sayfasında kaynak bağlantısı vardır.
Son derleme: {TARIH_TR}.</div></div>"""
        sss = [
            ("Öğretmenevi fiyatları 2026'da ne kadar?",
             f"Yayımlanmış {len(fiyatli)} tarifeye göre iki kişilik oda çoğunlukla "
             "1.500–3.000 TL, üç–dört kişilik oda 2.500–4.500 TL bandında. Tek bir "
             "ülke geneli fiyat yoktur; her tesis kendi tarifesini belirler."),
            ("Kamu personeli ile dışarıdan gelen misafir aynı ücreti mi öder?",
             "Hayır. Yayımlanmış listelerde çoğunlukla kurum personeli, diğer kamu "
             "personeli ve misafir için ayrı tarifeler bulunuyor."),
            ("Kahvaltı fiyata dahil mi?",
             "Yayımlanmış listelerin çoğunda açık büfe kahvaltının dahil olduğu "
             "belirtiliyor; ancak her tesiste geçerli değildir, teyit edilmelidir."),
        ]
        return govde, sss

    if anahtar == "denize-sifir-kamu-tesisleri":
        sat = sorted(deniz, key=lambda t: (t.get("ankara_saat") or 99, t["il"]))
        govde = f"""
<p>Bu dizindeki {len(tesisler)} tesisten <strong>{len(deniz)} tanesinin</strong>
denize konumu tesisin kendi yayınından doğrulandı. "Kıyı ilinde" olmakla "denize
yakın" olmak aynı şey değildir; aşağıdaki listede yalnızca konumu açıkça belirtilmiş
tesisler var.</p>
{_tablo(["Tesis", "İl / ilçe", "Denize konumu", "Ankara'dan"],
        [[_link(t), f'{e(t["il"])} / {e(t["ilce"])}', e(t["deniz"]),
          f'{e(t["ankara_saat"])} sa' if t.get("ankara_saat") else "—"] for t in sat])}
<h2>Ne zaman aramalı?</h2>
<p>Sahil tesislerinde temmuz–ağustos kontenjanı genellikle <strong>mayıs ayında</strong>
dolar. Haziran başı ve eylül, hem daha boş hem de çoğu tesiste daha ucuzdur.
Küçük çocukla gidiyorsanız havuzlu tesisler (bu listede
{sum(1 for t in deniz if any("havuz" in o.lower() for o in t.get("olanaklar") or []))}
tanesinde havuz kayıtlı) denizden daha kullanışlı olabiliyor.</p>
<div class="not">{ik("bilgi")}<div>Denize uzaklık tesisin kendi tanıtımından alınmıştır.
"Sahil şeridinde" ifadesi yürüme mesafesi anlamına gelir; kesin mesafe için tesisi arayın.</div></div>"""
        sss = [
            ("Denize sıfır öğretmenevi var mı?",
             "Evet. Bu dizinde denize konumu doğrulanmış "
             f"{len(deniz)} tesis var; bir kısmı doğrudan sahil şeridinde bulunuyor. "
             "Tam liste bu sayfadaki tabloda."),
            ("Sahil tesislerine ne zaman rezervasyon yaptırmalı?",
             "Temmuz–ağustos için mayıs ayında aramak gerekir; bu dönemde kontenjan "
             "hızla dolar. Haziran ve eylülde yer bulmak belirgin şekilde kolaydır."),
        ]
        return govde, sss

    if anahtar == "rezervasyon-nasil-yapilir":
        govde = f"""
<p>Kamu konaklama tesislerinin <strong>ortak bir rezervasyon sistemi yoktur</strong>.
Online rezervasyon alan tesis sayısı çok azdır; neredeyse tamamı telefonla çalışır.
Bu dizindeki {len(tesisler)} tesisin
{sum(1 for t in tesisler if t.get("telefon"))} tanesinin telefon numarası doğrulandı.</p>
<h2>Adım adım</h2>
<ol>
<li><strong>İli seçin.</strong> <a href="/il/">81 il listesinden</a> gideceğiniz ili açın.</li>
<li><strong>Tesisi açın.</strong> Her tesis sayfasında telefon, varsa e-posta ve yol tarifi var.</li>
<li><strong>Arayın.</strong> Kamu personeli olduğunuzu, kaç kişi ve hangi tarihler için
yer aradığınızı baştan söyleyin.</li>
<li><strong>Alternatif bırakın.</strong> Doluysa aynı ildeki diğer tesisleri sorun;
tesisler birbirini yönlendirir.</li>
<li><strong>Kaydı teyit edin.</strong> Rezervasyonu kimin adına, hangi tarihe aldıklarını
tekrar ettirin. Çoğu tesis kapora istemez.</li>
</ol>
<h2>Telefonda sorulacaklar</h2>
<ul>
<li>Şu tarihlerde iki yetişkin bir çocuk için oda var mı?</li>
<li>Kamu personeli tarifesi ne kadar, kahvaltı dahil mi?</li>
<li>Odada klima var mı, otopark ücretli mi?</li>
<li>Girişte hangi belgeleri getirmemiz gerekiyor?</li>
</ul>
<div class="not not-vurgu">{ik("bilgi")}<div><strong>E-posta da işe yarıyor.</strong>
Bu dizinde {sum(1 for t in tesisler if t.get("eposta"))} tesisin e-posta adresi var.
Telefonla ulaşılamayan tesislere yazılı sormak, özellikle tarih esnekliği varsa
sonuç veriyor.</div></div>"""
        sss = [
            ("Öğretmenevi rezervasyonu online yapılabilir mi?",
             "Çok az tesis online rezervasyon alır. Neredeyse tamamında rezervasyon "
             "tesisin kendi telefonundan yapılır; merkezî bir sistem yoktur."),
            ("Rezervasyon için kapora ödenir mi?",
             "Çoğu tesiste kapora istenmez, ödeme girişte yapılır. Yoğun sezonda bazı "
             "sahil tesisleri ön ödeme isteyebilir."),
            ("Kaç gün önceden aramak gerekir?",
             "Sezon dışında birkaç gün yeterlidir. Temmuz–ağustos sahil tesisleri için "
             "mayıs ayında aramak gerekir."),
        ]
        return govde, sss

    # ankaraya-yakin-deniz-tatili
    yakin = sorted(
        [t for t in tesisler if t.get("ankara_saat") and t["ankara_saat"] <= 7.5 and t.get("kiyi")],
        key=lambda t: t["ankara_saat"],
    )
    govde = f"""
<p>Ankara'dan arabayla <strong>7,5 saatin altında</strong> ulaşılabilen ve kıyı ilinde
bulunan {len(yakin)} kamu tesisi var. Süreler bilinen karayolu mesafelerinden
hesaplanan yaklaşık değerlerdir; mola dahil değildir.</p>
{_tablo(["Süre", "Tesis", "İl / ilçe", "Denize konumu"],
        [[f'<strong>{e(t["ankara_saat"])} sa</strong>', _link(t),
          f'{e(t["il"])} / {e(t["ilce"])}', e(t.get("deniz") or "—")] for t in yakin])}
<h2>Küçük çocukla gidiyorsanız</h2>
<p>İki yaş civarı bir çocukla <strong>beş saatin üstü tek seferde zor</strong>.
Tablodaki ilk sıralar (Karadeniz ve Marmara kıyısı) tek günde rahat gidilir;
Akdeniz kıyısı için yolu ikiye bölmek gerekir. Havuzlu tesisler denizden daha
kullanışlı olabiliyor: çocuk havuzu olan tesisler tesis sayfalarında ikonla işaretli.</p>
<div class="not">{ik("uyari")}<div>Mesafeler yaklaşıktır ve ölçülmemiştir; yalnızca
sıralama ve kabaca planlama için kullanılmalıdır.</div></div>"""
    sss = [
        ("Ankara'ya en yakın denize sıfır kamu tesisi hangisi?",
         (f"Bu dizindeki verilere göre Ankara'ya en yakın kıyı tesisi "
          f"{yakin[0]['ad']} ({yakin[0]['il']}), yaklaşık {yakin[0]['ankara_saat']} saat."
          if yakin else "Veri bulunamadı.")),
        ("Ankara'dan denize kaç saat sürer?",
         "En yakın kıyı tesisleri yaklaşık 4,5–5 saat mesafede. Akdeniz kıyısındaki "
         "tesisler 7 saat civarındadır."),
    ]
    return govde, sss


def rehber_sayfasi(anahtar: str, baslik: str, ikon: str, tesisler: list[dict]) -> str:
    yol = f"/rehber/{anahtar}/"
    govde, sss = rehber_govde(anahtar, tesisler)
    kirintilar = [("/", "Ana sayfa"), ("/rehber/", "Rehber"), (yol, baslik)]

    icerik = f"""<div class="kap" style="max-width:760px;padding-block:34px 0">
<span class="rz rz-vurgu">{ik(ikon)}Rehber</span>
<h1 style="margin:12px 0 10px">{e(baslik)}</h1>
<p style="color:var(--soluk);font-size:.9rem;margin:0 0 26px">
{ik("saat")} Son güncelleme: {TARIH_TR} · {len(tesisler)} tesislik veri kümesinden derlendi</p>
<div class="yazi">{govde}
<h2>Sık sorulan sorular</h2></div>
{sss_html(sss)}
<div class="not" style="margin:26px 0 40px">{ik("bilgi")}<div>
Bu sayfa bağımsız bir dizin tarafından hazırlanmıştır ve resmî bir kaynak değildir.
Bağlayıcı bilgi için tesisin bağlı olduğu kuruma başvurun.</div></div>
</div>"""

    ld = {
        "@context": "https://schema.org",
        "@type": "Article",
        "headline": baslik,
        "datePublished": "2026-08-29",
        "dateModified": BUGUN.isoformat(),
        "inLanguage": "tr-TR",
        "isAccessibleForFree": True,
        "publisher": {"@type": "Organization", "name": AD, "url": SITE},
        "mainEntityOfPage": SITE + yol,
    }
    return kabuk(
        baslik=f"{baslik} | {AD}",
        aciklama=REHBER_OZET[anahtar][:158],
        yol=yol,
        icerik=icerik,
        kirintilar=kirintilar,
        aktif="/rehber/",
        jsonld=[ld, sss_ld(sss), kirinti_ld(kirintilar)],
    )


def rehber_dizini(tesisler: list[dict]) -> str:
    kartlar = ""
    for s, baslik, ikon in REHBERLER:
        kartlar += f"""<article class="tk rehber-k"><div class="tk-govde" style="padding:20px 20px 0">
<span class="rz rz-vurgu">{ik(ikon)}Rehber</span>
<h3 class="tk-ad" style="margin-top:10px"><a href="/rehber/{s}/">{e(baslik)}</a></h3>
<p style="font-size:.92rem;color:var(--soluk)">{e(REHBER_OZET[s])}</p></div>
<div class="tk-alt"><span class="dg dg-3 dg-sm" style="padding:0">Oku{ik("ok")}</span></div></article>"""
    kirintilar = [("/", "Ana sayfa"), ("/rehber/", "Rehber")]
    icerik = f"""<section class="bl kap">
<div class="bl-bas"><div><h1>Rehber</h1>
<p>Kimler kalabilir, fiyatlar ne kadar, rezervasyon nasıl yapılır — hepsi
{len(tesisler)} tesislik veri kümesinden derlendi, tahmin yok.</p></div></div>
<div class="iz">{kartlar}</div></section>"""
    return kabuk(
        baslik=f"Rehber — kamu misafirhanelerinde konaklama | {AD}",
        aciklama="Öğretmenevi ve kamu misafirhanelerinde kimler kalabilir, fiyatlar, "
        "rezervasyon ve denize yakın tesisler hakkında veriye dayalı rehberler.",
        yol="/rehber/",
        icerik=icerik,
        kirintilar=kirintilar,
        aktif="/rehber/",
        jsonld=[kirinti_ld(kirintilar)],
    )
