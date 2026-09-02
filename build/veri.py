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
    """Benzersiz, 65 karakteri aşmayan sayfa başlığı."""
    ad = kisa_ad(t["ad"])
    yer = t["il"] if t["ilce"].lower() in ad.lower() else f"{t['ilce']}, {t['il']}"
    for aday in (f"{ad}, {yer} — telefon ve fiyat", f"{ad}, {yer}", f"{ad}, {t['il']}", ad):
        if len(aday) <= 68:
            return aday
    return ad


_TUTAR = re.compile(r"\b(\d{1,3}(?:\.\d{3})+|\d{3,6})\b")


def fiyat_taban(metin: str | None) -> int:
    """Yayımlanan fiyat metnindeki en düşük gerçekçi tutar.

    Metinlerde birden çok oda tipi geçiyor ("2 kişilik 3.000 / 4 kişilik 4.000 TL").
    Sıralama için en düşük tutarı almak, "şu fiyattan başlıyor" anlamına gelir ve
    yanıltmaz; en büyüğü almak dört kişilik odayı tek kişilik gibi gösterirdi.
    Yıl sayıları (2026) ve küçük rakamlar elenir.
    """
    if not metin:
        return 0
    tutarlar = []
    for ham in _TUTAR.findall(metin):
        try:
            n = int(ham.replace(".", ""))
        except ValueError:
            continue
        if 500 <= n <= 200000 and not (2000 <= n <= 2100 and "." not in ham):
            tutarlar.append(n)
    return min(tutarlar) if tutarlar else 0


def fiyat_araligi(metin: str | None) -> tuple[int, int]:
    """Yayımlanan fiyat metnindeki en düşük ve en yüksek gerçekçi tutar.

    schema.org priceRange için gerekiyor. fiyat_taban ile aynı süzgeci
    kullanır; tek tutar varsa iki uç da odur.
    """
    if not metin:
        return (0, 0)
    tutarlar = []
    for ham in _TUTAR.findall(metin):
        try:
            n = int(ham.replace(".", ""))
        except ValueError:
            continue
        if 500 <= n <= 200000 and not (2000 <= n <= 2100 and "." not in ham):
            tutarlar.append(n)
    return (min(tutarlar), max(tutarlar)) if tutarlar else (0, 0)


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
