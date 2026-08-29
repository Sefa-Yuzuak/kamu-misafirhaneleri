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


def telefon_link(no: str) -> str:
    return "tel:+9" + re.sub(r"\D", "", no)


def baslik_duzelt(ad: str) -> str:
    """Uzun resmi adları kısaltmadan, ekranda okunur hale getirir."""
    return re.sub(r"\s+", " ", ad).strip()
