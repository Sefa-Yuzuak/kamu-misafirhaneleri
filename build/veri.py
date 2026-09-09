"""Ortak yardımcılar: slug, tür bilgisi, tesis anahtarı."""

from __future__ import annotations

import re
import unicodedata

_HARF = str.maketrans(
    {
        "ç": "c", "Ç": "c", "ğ": "g", "Ğ": "g", "ı": "i", "I": "i",
        "İ": "i", "i": "i", "ö": "o", "Ö": "o", "ş": "s", "Ş": "s",
        "ü": "u", "Ü": "u", "â": "a", "î": "i", "û": "u",
    }
)


def slug(metin: str) -> str:
    s = metin.translate(_HARF).lower()
    s = unicodedata.normalize("NFKD", s).encode("ascii", "ignore").decode()
    s = re.sub(r"[^a-z0-9]+", "-", s)
    return s.strip("-")


def tesis_slug(t: dict) -> str:
    """Tesis adresi. İl eklenir; aynı adlı tesisler farklı illerde var."""
    return f"{slug(t['il'])}-{slug(t['ad'])}"[:90].strip("-")


# tür -> (çoğul başlık, kısa ad, ikon anahtarı, açıklama)
TURLER = {
    "Öğretmenevi": (
        "Öğretmenevleri",
        "Öğretmenevi",
        "okul",
        "Milli Eğitim Bakanlığı'na bağlı, öğretmenler ve diğer kamu personeli ile "
        "birinci derece yakınlarının konaklayabildiği tesisler.",
    ),
    "Polisevi": (
        "Polisevleri",
        "Polisevi",
        "kalkan",
        "Emniyet Genel Müdürlüğü'ne bağlı, emniyet mensupları ve kamu personelinin "
        "konaklayabildiği moral eğitim merkezleri.",
    ),
    "Üniversite Misafirhanesi": (
        "Üniversite Misafirhaneleri",
        "Üniversite",
        "bina",
        "Üniversitelerin akademik ve idari personel ile kamu görevlilerine açık "
        "sosyal tesis ve misafirhaneleri.",
    ),
    "Kamu Misafirhanesi": (
        "Kamu Misafirhaneleri",
        "Kamu",
        "bayrak",
        "Bakanlık, genel müdürlük ve kamu kurumlarının kendi personeli ile diğer "
        "kamu görevlilerine açık konaklama tesisleri.",
    ),
}


def tur_slug(tur: str) -> str:
    return slug(TURLER[tur][0])


def ulusal_rakam(no: str) -> str:
    """Yalnız rakamlar, baştaki 0 atılmış: "0322 453 31 58" -> "3224533158"."""
    d = re.sub(r"\D", "", no)
    return d[1:] if d.startswith("0") else d


def e164(no: str) -> str:
    """Uluslararası biçim: "0322 453 31 58" -> "+903224533158".

    Türkiye ülke kodu 90'dır. Baştaki 0 atıldıktan sonra "+9" eklenirse
    "+9322…" çıkıyordu ve telefon uygulaması yanlış numara çeviriyordu.
    """
    return "+90" + ulusal_rakam(no)


def wa_numarasi(no: str) -> str:
    """wa.me biçimi: artı işaretsiz, "903224533158"."""
    return "90" + ulusal_rakam(no)


def telefon_link(no: str) -> str:
    return "tel:" + e164(no)


_UZANTI = re.compile(
    r"\s*(ve\s+)?(Akşam|Aksam)\s+Sanat\s+Ok(ulu|\.)?ı?"
    r"(\s+İktisadi\s+İşletmesi)?\s*$",
    re.IGNORECASE,
)
_IKTISADI = re.compile(r"\s*İktisadi\s+İşletmesi\s*$", re.IGNORECASE)


def kisa_ad(ad: str) -> str:
    """Ekranda ve başlıkta kullanılan ad. Resmî ad künye tablosunda kalır.

    521 öğretmenevinin resmî adı "... ve Akşam Sanat Okulu" ile bitiyor; bu ek
    her başlığı 21 karakter uzatıp arama sonucunda kırpılmasına yol açıyor.
    """
    kisa = re.sub(r"\s+", " ", ad).strip()
    for _ in range(3):
        yeni = _IKTISADI.sub("", _UZANTI.sub("", kisa)).strip(" ,-")
        if yeni == kisa:
            break
        kisa = yeni
    return kisa or ad


def sayfa_basligi(t: dict) -> str:
    """Benzersiz, 62 karakteri asmayan sayfa basligi.

    ESKI HALI HER SAYFAYA " — telefon ve fiyat" yaziyordu. OLCULDU: 562 tesisin
    yalnizca 21'inde yayimlanmis fiyat var, yani 541 sayfa SERP'te tutamayacagi
    bir soz veriyordu. Ustelik ayni ek her sayfada tekrarlandigi icin baslik
    hicbir tesisi digerinden ayirmiyordu; Search Console'da tesis sayfalarinin
    TO'su %0,3-1,7 arasinda (konum 7-13 iken) olculdu.

    Artik vaat, kaydin GERCEKTEN tasidigi bilgiye gore seciliyor. Tesis adi
    hicbir zaman kirpilmiyor: yarim bir ad baska tesisi gosterir.
    """
    ad = kisa_ad(t["ad"])
    # Bos ilce `"" in ad` -> True verdigi icin yer=il oluyordu ve adi zaten
    # ili iceren tesislerde "Ankara Polisevi, Ankara" gibi tekrar cikiyordu.
    if not t.get("ilce"):
        yer = "" if t["il"].lower() in ad.lower() else t["il"]
    elif t["ilce"].lower() in ad.lower():
        yer = t["il"]
    else:
        yer = f"{t['ilce']}, {t['il']}"
    # Alanda metin olmasi yetmez, icinde TUTAR olmali: iki kayitta "2026
    # donemleri 1 Haziran-27 Eylul" gibi bir NOT yaziliydi ve sayfa hic fiyat
    # tasimadigi halde basligi "2026 fiyati" diye soz veriyordu.
    if fiyat_taban(t.get("fiyat_2026")):
        ekler = (" — 2026 fiyatı ve telefon", " — fiyat ve telefon", " — fiyat")
    elif t.get("deniz"):
        ekler = (" — denize yakın, telefon", " — denize yakın", "")
    elif t.get("adres") and t.get("telefon"):
        # Ölçüldü: "adres/yol" niyetli 71 sorgu 217 gösterim alıyor ve TO %0,
        # ortalama konum 18,7 — çünkü sayfada adres YOKTU. Artık 514 tesiste
        # kurumun kendi yayımladığı açık adres var, vaat gerçek.
        ekler = (" — adres ve telefon", " — adres", " — telefon")
    elif t.get("telefon"):
        ekler = (" — telefon ve konaklama", " — telefon", "")
    else:
        ekler = ("",)
    for ek in ekler:
        for y in (yer, t["il"], ""):
            govde = ", ".join(x for x in (ad, y) if x)
            aday = f"{govde}{ek}"
            if len(aday) <= 62:
                return aday
    return ad


# Tutar YALNIZCA para birimiyle birlikte sayilir. Eski desen ciplak sayilari da
# aliyordu ve "212 Nolu Oda" satirindaki 212'yi fiyat sanabiliyordu; ustelik yil
# sayilarini elemek icin ayri bir kural gerekiyordu. Para birimi sarti ikisini de
# cozuyor. Alt sinir 500'den 150'ye indi: kurumlarin kendi yayimladigi
# tarifelerde 250-450 TL'lik yatak ucretleri var ve 500 esigi bunlari GORMUYORDU.
_TUTAR = re.compile(
    r"(\d{1,3}(?:\.\d{3})+|\d{3,6})(?:[,.]\d{2})?\s*(?:TL|₺)", re.I)
# Donemlik paketler gecelik tarifelerle karsilastirilamaz: "6 gece 7 gun 50.400 TL"
# bir gecelik fiyat degildir ve "en ucuz" siralamasina girerse tabloyu bozar.
_DONEMLIK = re.compile(r"(\d+\s*gece|dönem sistemi|haftalık|sezonluk)", re.I)


def _tutarlar(metin: str | None) -> list[int]:
    if not metin:
        return []
    cikti = []
    for ham in _TUTAR.findall(metin):
        try:
            n = int(ham.replace(".", ""))
        except ValueError:
            continue
        if 150 <= n <= 200000:
            cikti.append(n)
    return cikti


def donemlik_mi(metin: str | None) -> bool:
    """Fiyat gecelik degil, cok geceli paket mi?"""
    return bool(metin) and bool(_DONEMLIK.search(metin))


def fiyat_taban(metin: str | None) -> int:
    """Yayimlanan fiyat metnindeki en dusuk gercekci tutar.

    Metinlerde birden cok oda tipi geciyor ("2 kisilik 3.000 / 4 kisilik 4.000 TL").
    Siralama icin en dusugu almak "su fiyattan basliyor" anlamina gelir ve
    yaniltmaz; en buyugu almak dort kisilik odayi tek kisilik gibi gosterirdi.
    """
    t = _tutarlar(metin)
    return min(t) if t else 0


def fiyat_araligi(metin: str | None) -> tuple[int, int]:
    """schema.org priceRange icin en dusuk ve en yuksek tutar."""
    t = _tutarlar(metin)
    return (min(t), max(t)) if t else (0, 0)


_SESLI = "aeıioöuü"
_KALIN = "aıou"
_SERT = "fstkçşhp"


def _son_sesli(ad: str) -> str:
    for h in reversed(ad.lower()):
        if h in _SESLI:
            return h
    return "a"


def yonelme(ad: str) -> str:
    """Yönelme hâli: Ankara -> Ankara'ya, İstanbul -> İstanbul'a, İzmir -> İzmir'e."""
    kalin = _son_sesli(ad) in _KALIN
    kaynastirma = "y" if ad and ad[-1].lower() in _SESLI else ""
    return f"{ad}'{kaynastirma}{'a' if kalin else 'e'}"


def cikma(ad: str) -> str:
    """Ayrılma hâli: Ankara -> Ankara'dan, İzmir -> İzmir'den, Sinop -> Sinop'tan."""
    kalin = _son_sesli(ad) in _KALIN
    d = "t" if ad and ad[-1].lower() in _SERT else "d"
    return f"{ad}'{d}{'a' if kalin else 'e'}n"


# --- Türkçe güvenli harf dönüşümü -------------------------------------------
# Python'un kendi lower()/title()'ı Türkçeyi bozar: "KONUKEVİ".title() ->
# "Konukevi̇" (İ, i + U+0307 birleşen noktaya ayrışır) ve "IĞDIR".lower() ->
# "iğdir". Dönüşümden ÖNCE noktalı/noktasız i çiftini elle eşlemek gerekir.
_KUCULT = str.maketrans("İI", "iı")
_BUYULT = str.maketrans("iı", "İI")


def tr_kucuk(metin: str) -> str:
    return metin.translate(_KUCULT).lower()


def tr_buyuk(metin: str) -> str:
    return metin.translate(_BUYULT).upper()


# BÜYÜK harfte İ ile I ayrımı kaybolur ve geri getirilemez: "MİLLİ" de "MILLI"
# de aynı tuşla yazılıyor. 488 adresteki 178 farklı belirsiz sözcük sayıldı ve
# ÇOĞUNDA noktasız ı DOĞRU çıktı (KAPI, ÇANKIRI, HACI, BALIKESİR, AĞRI...).
# Bu yüzden varsayılan kural I -> ı; aşağıdaki liste yalnızca ölçülen istisnalar.
_NOKTALI = {
    "EVI": "Evi", "ÖĞRETMENEVI": "Öğretmenevi", "OGRETMENEVI": "Öğretmenevi",
    "EĞITIM": "Eğitim", "EGITIM": "Eğitim", "MILLI": "Millî", "BINASI": "Binası",
    "ŞEHIT": "Şehit", "SEHIT": "Şehit", "FAKIH": "Fakih", "HIZMET": "Hizmet",
    "ILCE": "İlçe", "ILÇE": "İlçe", "ISKELE": "İskele", "CUMHURIYET": "Cumhuriyet",
    "BURHANIYE": "Burhaniye", "ERZIN": "Erzin", "ERZINCAN": "Erzincan",
    "LISESI": "Lisesi", "MERKEZI": "Merkezi", "MERZIFON": "Merzifon",
    "MECITÖZÜ": "Mecitözü", "NISAN": "Nisan", "PANSIYON": "Pansiyon",
    "PANSIYONU": "Pansiyonu", "TESIS": "Tesis", "TURIZM": "Turizm",
    "UNIVERSITESI": "Üniversitesi", "SELAHATTIN": "Selahattin",
    "İBRAHIM": "İbrahim", "ÖĞRENCI": "Öğrenci", "KARESIBEY": "Karesibey",
    "BALIKESIR": "Balıkesir", "PIRAZIZ": "Piraziz", "ÇIFTÇI": "Çiftçi",
    "FEVZIATAC": "Fevziatac", "ILIC": "İliç", "ŞEREFLIKOÇHISAR": "Şereflikoçhisar",
}


def tr_baslik(metin: str) -> str:
    """Yalnızca TAMAMI büyük yazılmış sözcükleri düzeltir.

    Zaten doğru yazılmış sözcüğe dokunulmaz; "Kurtuluş Mahallesi ... / HATAY"
    gibi karışık yazımlarda sadece bağıran parça yumuşar.
    """
    cikti = []
    for s in metin.split(" "):
        cekirdek = s.strip(".,;:/()-")
        if cekirdek.upper() in _NOKTALI and cekirdek == tr_buyuk(cekirdek):
            s = s.replace(cekirdek, _NOKTALI[cekirdek.upper()])
        elif len([h for h in s if h.isalpha()]) > 1 and s == tr_buyuk(s):
            s = tr_buyuk(s[:1]) + tr_kucuk(s[1:])
        cikti.append(s)
    return " ".join(cikti)


_ADRES_GURULTU = re.compile(
    r"\s*(İÇ\s*KAPI\s*NO[:\s]*\S+|D(ış|IŞ)\s*[Kk]ap[ıi]\s*[Nn]o[:\s]*\S+"
    r"|BLOK\s*NO[:\s]*\S+|[Aa]dres\s*no\s*\d+|POSTA\s*KODU.*|PK\s*\d+)",
    re.I)
# Adres alanina sonradan yapisan kuyruklar: kurum sayfalarinda telefon, e-posta
# ve web adresi cogu zaman ayni satira devam ediyor.
_ADRES_KUYRUK = re.compile(
    r"\s*[-–—,]?\s*(telefon|tel\.?|gsm|faks|belgege[çc]er|e-?posta|eposta|"
    r"e-?mail|web\s*adresi|https?://).*$", re.I)
# Etiketsiz telefon: "... Adana Seyhan Öğretmenevi 0322 453 31 58 - 0533 ..."
_ADRES_TEL = re.compile(r"\s*[-–—,]?\s*0\d{3}[\s\-]?\d{3}[\s\-]?\d{2}[\s\-]?\d{2}.*$")
# Basa yapisan tam cumle: "Eskisehir merkeze 65 km uzakta. Sakarya Mah. ..."
_ADRES_ONEK = re.compile(r"^[^.]{20,}?\.\s+(?=\S+\s+(mah|mh|mahalle))", re.I)


def duzgun_adres(adres: str) -> str:
    """Ekranda gösterilecek biçim: bağırmayan, iç kapı/blok gürültüsü atılmış."""
    a = _ADRES_ONEK.sub("", (adres or "").strip())
    a = _ADRES_GURULTU.sub("", _ADRES_TEL.sub("", _ADRES_KUYRUK.sub("", a)))
    a = re.sub(r"\s*/\s*", " / ", re.sub(r"\s+", " ", a)).strip(" ,;-/")
    return tr_baslik(a)


def adres_ozeti(adres: str, en: int = 52) -> str:
    """Açıklamada kullanılan kısa adres: mahalle + cadde, ilçe/il kuyruğu yok.

    Kuyruk zaten cümlenin başında "(İlçe, İl)" olarak geçiyor; tekrarlamak
    açıklamanın sınırlı 158 karakterini harcar.
    """
    a = duzgun_adres(adres)
    a = re.sub(r"\s*/\s*[^/]+$", "", a)              # "... Söğüt / Bilecik" kuyruğu
    a = re.sub(r"\s*No[:.]?\s*\S+\s*$", "", a, flags=re.I)
    a = a.strip(" ,;-")
    if len(a) <= en:
        return a
    return a[:en].rsplit(" ", 1)[0].rstrip(" ,;-.")
