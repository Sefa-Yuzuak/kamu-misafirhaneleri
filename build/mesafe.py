"""Koordinatlardan mesafe hesabı.

Elimizde ölçülmüş karayolu mesafesi yok; kuş uçuşu mesafeyi Türkiye yol ağı için
bir sapma katsayısıyla çarpıyoruz. Sonuç **tahmindir** ve sayfada böyle etiketlenir.

Katsayı, bilinen güzergâhlarla karşılaştırılarak seçildi:
    Ankara–Sinop     kuş uçuşu 320 km / karayolu ~420 km  -> 1,31
    Ankara–İstanbul  kuş uçuşu 350 km / karayolu ~450 km  -> 1,29
    Ankara–Antalya   kuş uçuşu 380 km / karayolu ~480 km  -> 1,26
    Ankara–İzmir     kuş uçuşu 520 km / karayolu ~590 km  -> 1,13
"""

from __future__ import annotations

import math
from collections import defaultdict

SAPMA = 1.27  # kuş uçuşu -> karayolu tahmini
ORT_HIZ = 78.0  # km/sa, mola hariç

# Araç sayfalarında ve tablolarda kullanılan başlıca çıkış noktaları
CIKIS_NOKTALARI = [
    ("Ankara", 39.9208, 32.8541),
    ("İstanbul", 41.0082, 28.9784),
    ("İzmir", 38.4237, 27.1428),
]


def kus_ucusu(a: tuple[float, float], b: tuple[float, float]) -> float:
    """İki nokta arası büyük daire mesafesi, km."""
    lat1, lon1 = math.radians(a[0]), math.radians(a[1])
    lat2, lon2 = math.radians(b[0]), math.radians(b[1])
    dlat, dlon = lat2 - lat1, lon2 - lon1
    h = math.sin(dlat / 2) ** 2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon / 2) ** 2
    return 6371.0 * 2 * math.asin(math.sqrt(h))


def karayolu_km(a: tuple[float, float], b: tuple[float, float]) -> int:
    """Tahmini karayolu mesafesi, km. 5'in katına yuvarlanır — sahte hassasiyet olmasın."""
    km = kus_ucusu(a, b) * SAPMA
    return int(round(km / 5.0) * 5)


def sure_saat(km: float) -> float:
    """Tahmini sürüş süresi, yarım saate yuvarlı."""
    return round(km / ORT_HIZ * 2) / 2


def sure_metni(saat: float) -> str:
    if saat < 1:
        return f"{int(saat * 60)} dk"
    tam = int(saat)
    dakika = int(round((saat - tam) * 60))
    return f"{tam} sa" + (f" {dakika} dk" if dakika else "")


def il_merkezleri(konumlar: dict) -> dict[str, tuple[float, float]]:
    """İl adı -> o ildeki tesis konumlarının ortalaması.

    Ölçülmüş il merkezi değil; "bu ilden yola çıkarsam" hesabı için yeterli
    bir temsil noktası. Araç sayfasında bu açıkça yazılır.
    """
    toplam: dict[str, list[tuple[float, float]]] = defaultdict(list)
    for v in konumlar.values():
        if v and v.get("il"):
            toplam[v["il"]].append((v["lat"], v["lon"]))
    return {
        il: (sum(x for x, _ in n) / len(n), sum(y for _, y in n) / len(n))
        for il, n in toplam.items()
    }


def en_yakinlar(
    hedef_slug: str, konumlar: dict, adet: int = 6
) -> list[tuple[str, int]]:
    """Bir tesise en yakın diğer tesisler: [(slug, km), ...]"""
    k = konumlar.get(hedef_slug)
    if not k:
        return []
    nokta = (k["lat"], k["lon"])
    mesafeler = []
    for s, v in konumlar.items():
        if s == hedef_slug or not v:
            continue
        mesafeler.append((s, karayolu_km(nokta, (v["lat"], v["lon"]))))
    mesafeler.sort(key=lambda x: x[1])
    return mesafeler[:adet]


def cikis_mesafeleri(konum: dict) -> list[tuple[str, int, float]]:
    """[(şehir, km, saat), ...] — başlıca çıkış noktalarından."""
    nokta = (konum["lat"], konum["lon"])
    cikti = []
    for ad, lat, lon in CIKIS_NOKTALARI:
        km = karayolu_km(nokta, (lat, lon))
        if km >= 15:  # aynı şehirdeyse anlamsız
            cikti.append((ad, km, sure_saat(km)))
    return cikti
