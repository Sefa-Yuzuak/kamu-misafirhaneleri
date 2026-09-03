"""İllerin yöresel yemeklerini Vikipedi'den toplar.

Yaklaşım gezi.py ile aynı: uydurma yok, her kayıt Vikipedi'de gerçekten var
olan bir maddedir ve kaynağı sayfada gösterilir (CC BY-SA 4.0).

Kaynak `Kategori:{İl} mutfağı`. 81 ilin hepsinde bu kategori yok; olmayan il
için liste boş kalır ve sayfada yemek bölümü hiç çıkmaz — "bu ilde şu yenir"
diye tahmin yürütülmez.

    python build/mutfak.py
"""

from __future__ import annotations

import json
import re
import sys
import time
import urllib.parse
import urllib.request
from pathlib import Path

KOK = Path(__file__).resolve().parent.parent
HEDEF = KOK / "data" / "mutfak.json"
UA = {"User-Agent": "kamumisafirhaneler.com/1.0 (https://kamumisafirhaneler.com)"}
API = "https://tr.wikipedia.org/w/api.php?"

#: Kategoriye girmiş ama yemek olmayan maddeler: kitap, müze, festival,
#: kurum ve kategorinin kendi ana maddesi ("Gaziantep mutfağı").
_ELE = re.compile(
    r"mutfağı$|müzesi|festival|üniversite|kültür merkezi|derneği|"
    r"yarışması|geçmişten geleceğe|listesi",
    re.IGNORECASE,
)
#: En fazla kaç yemek saklanır (sayfada hepsi gösterilmez, seçim yapılır)
EN_COK = 24


def _api(params: dict) -> dict:
    p = {"format": "json", "formatversion": "2", **params}
    url = API + urllib.parse.urlencode(p)
    with urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=30) as r:
        return json.load(r)


def kategori_uyeleri(il: str) -> list[str]:
    d = _api({
        "action": "query", "list": "categorymembers",
        "cmtitle": f"Kategori:{il} mutfağı", "cmlimit": 50, "cmtype": "page",
    })
    uyeler = d.get("query", {}).get("categorymembers", [])
    return [u["title"] for u in uyeler if not _ELE.search(u["title"])]


def ayrinti(basliklar: list[str]) -> dict[str, dict]:
    """Başlık -> {ozet, aciklama}. En fazla 20 başlık tek istekte."""
    if not basliklar:
        return {}
    d = _api({
        "action": "query", "titles": "|".join(basliklar[:20]),
        "prop": "extracts|pageterms", "exintro": "1", "explaintext": "1",
        "exsentences": "2",
    })
    cikti = {}
    for s in d.get("query", {}).get("pages", []):
        if s.get("missing"):
            continue
        terim = s.get("terms") or {}
        ozet = re.sub(r"\s+", " ", (s.get("extract") or "")).strip()
        if len(ozet) < 40:  # taslak madde: tanıtacak bilgi yok
            continue
        cikti[s["title"]] = {
            "ozet": ozet[:300],
            "aciklama": (terim.get("description") or [""])[0][:110],
        }
    return cikti


def main() -> int:
    tesisler = json.loads((KOK / "tesisler.json").read_text("utf-8"))["tesisler"]
    iller = sorted({t["il"] for t in tesisler})
    sonuc = json.loads(HEDEF.read_text("utf-8")) if HEDEF.exists() else {}

    for i, il in enumerate(iller, 1):
        if il in sonuc:
            continue
        try:
            basliklar = kategori_uyeleri(il)
            time.sleep(0.25)
            ayr: dict[str, dict] = {}
            for j in range(0, min(len(basliklar), EN_COK), 20):
                ayr.update(ayrinti(basliklar[j:j + 20]))
                time.sleep(0.25)
            yemekler = [
                {"ad": ad, "ozet": v["ozet"], "aciklama": v["aciklama"]}
                for ad, v in ayr.items()
            ]
            sonuc[il] = yemekler
            print(f"{i:2}/{len(iller)} {il:16} {len(yemekler):2} yemek")
        except Exception as ex:
            print(f"{i:2}/{len(iller)} {il:16} HATA {type(ex).__name__}: {ex}")
            sonuc.setdefault(il, [])
        if i % 10 == 0 or i == len(iller):
            HEDEF.write_text(json.dumps(sonuc, ensure_ascii=False), "utf-8")

    HEDEF.write_text(json.dumps(sonuc, ensure_ascii=False), "utf-8")
    dolu = sum(1 for v in sonuc.values() if v)
    toplam = sum(len(v) for v in sonuc.values())
    print(f"\n{dolu}/{len(sonuc)} ilde toplam {toplam} yöresel yemek")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
