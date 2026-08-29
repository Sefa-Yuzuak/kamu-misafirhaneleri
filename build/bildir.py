"""Yeni ve değişen sayfaları arama motorlarına bildirir.

    python build/bildir.py dogrula     alan adını Search Console'a doğrula ve ekle
    python build/bildir.py sitemap     site haritasını Google'a gönder
    python build/bildir.py indexnow    adresleri Bing/Yandex'e bildir
    python build/bildir.py durum       doğrulama ve gönderim durumunu göster

Google tarafı, gcloud'un uygulama varsayılan kimlik bilgisini kullanır:
    gcloud auth application-default login --scopes=...webmasters,...siteverification
IndexNow anahtar gerektirmez; anahtar dosyası site kökünde yayımlanır.

Not: Satın alınan ya da toplu üretilen bağlantı Google'ın bağlantı spamı
politikasına aykırıdır. Burada yalnızca içeriğin arama motorlarına bildirilmesi
yapılır; bağlantı üretimi yoktur.
"""

from __future__ import annotations

import json
import subprocess
import sys
import urllib.error
import urllib.request
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from dagitim import INDEXNOW_ANAHTAR, INDEXNOW_SUNUCULARI  # noqa: E402
from parca import SITE  # noqa: E402

KOK = Path(__file__).resolve().parent.parent
ALAN = SITE.replace("https://", "")
PROJE = "vitrin-analytics"
GCLOUD = (
    r"C:\Users\Admin\AppData\Local\Google\Cloud SDK\google-cloud-sdk\bin\gcloud.cmd"
)


def belirtec() -> str:
    yol = GCLOUD if Path(GCLOUD).exists() else "gcloud"
    r = subprocess.run(
        [yol, "auth", "application-default", "print-access-token"],
        capture_output=True, text=True, shell=False,
    )
    if r.returncode != 0:
        raise SystemExit(
            "Erişim belirteci alınamadı. Şunu çalıştırın:\n"
            "  gcloud auth application-default login --scopes="
            "openid,https://www.googleapis.com/auth/userinfo.email,"
            "https://www.googleapis.com/auth/cloud-platform,"
            "https://www.googleapis.com/auth/webmasters,"
            "https://www.googleapis.com/auth/siteverification"
        )
    return r.stdout.strip()


def _istek(url: str, yontem: str = "GET", govde: dict | None = None,
           tok: str | None = None) -> tuple[int, dict]:
    veri = json.dumps(govde).encode() if govde is not None else None
    istek = urllib.request.Request(url, data=veri, method=yontem)
    istek.add_header("Content-Type", "application/json")
    if tok:
        istek.add_header("Authorization", f"Bearer {tok}")
        istek.add_header("x-goog-user-project", PROJE)
    try:
        with urllib.request.urlopen(istek, timeout=40) as r:
            ham = r.read().decode() or "{}"
            return r.status, json.loads(ham) if ham.strip() else {}
    except urllib.error.HTTPError as ex:
        ham = ex.read().decode()
        try:
            return ex.code, json.loads(ham)
        except json.JSONDecodeError:
            return ex.code, {"metin": ham[:300]}


# --------------------------------------------------------------------------
def dogrula() -> int:
    tok = belirtec()
    print("1) Alan adı doğrulaması (DNS TXT)")
    kod, d = _istek(
        "https://www.googleapis.com/siteVerification/v1/webResource?verificationMethod=DNS_TXT",
        "POST",
        {"site": {"type": "INET_DOMAIN", "identifier": ALAN}},
        tok,
    )
    if kod == 200:
        print("   doğrulandı:", d.get("id"))
    else:
        print(f"   olmadı ({kod}):", str(d.get("error", {}).get("message", d))[:180])
        kod2, d2 = _istek(
            "https://www.googleapis.com/siteVerification/v1/token", "POST",
            {"site": {"type": "INET_DOMAIN", "identifier": ALAN},
             "verificationMethod": "DNS_TXT"}, tok,
        )
        if kod2 == 200:
            print("\n   DNS'e şu TXT kaydı eklenmeli:")
            print(f"     Ad   : {ALAN}  (ya da @)")
            print(f"     Tür  : TXT")
            print(f"     Değer: {d2['token']}")
            print("   Kayıt yayıldıktan sonra bu komut tekrar çalıştırılmalı.")

    print("\n2) Adres öneki doğrulaması (sayfadaki META etiketi)")
    kod, d = _istek(
        "https://www.googleapis.com/siteVerification/v1/webResource?verificationMethod=META",
        "POST",
        {"site": {"type": "SITE", "identifier": SITE + "/"}},
        tok,
    )
    print(("   doğrulandı: " + str(d.get("id"))) if kod == 200
          else f"   olmadı ({kod}): {str(d.get('error', {}).get('message', d))[:180]}")

    print("\n3) Search Console'a ekleme")
    for hedef in (f"sc-domain:{ALAN}", SITE + "/"):
        kod, d = _istek(
            "https://www.googleapis.com/webmasters/v3/sites/"
            + urllib.request.quote(hedef, safe=""),
            "PUT", None, tok,
        )
        print(f"   {hedef:44} {'eklendi' if kod in (200, 204) else f'olmadı ({kod})'}")
    return 0


def sitemap_gonder() -> int:
    tok = belirtec()
    harita = urllib.request.quote(SITE + "/sitemap.xml", safe="")
    gonderildi = 0
    for hedef in (f"sc-domain:{ALAN}", SITE + "/"):
        h = urllib.request.quote(hedef, safe="")
        kod, d = _istek(
            f"https://www.googleapis.com/webmasters/v3/sites/{h}/sitemaps/{harita}",
            "PUT", None, tok,
        )
        if kod in (200, 204):
            print(f"   {hedef:44} site haritası gönderildi")
            gonderildi += 1
        else:
            print(f"   {hedef:44} olmadı ({kod}) "
                  f"{str(d.get('error', {}).get('message', ''))[:90]}")
    if not gonderildi:
        print("\n   Önce doğrulama gerekiyor: python build/bildir.py dogrula")
    return 0


def indexnow(adet: int = 10000) -> int:
    yol = KOK / "site" / "urls.txt"
    if not yol.exists():
        raise SystemExit("site/urls.txt yok — önce build/derle.py çalıştırın")
    adresler = [s for s in yol.read_text("utf-8").split("\n") if s.strip()][:adet]
    govde = {
        "host": ALAN,
        "key": INDEXNOW_ANAHTAR,
        "keyLocation": f"{SITE}/{INDEXNOW_ANAHTAR}.txt",
        "urlList": adresler,
    }
    # Yeni alan adında toplu POST 403 donuyor: anahtar henuz taninmiyor.
    # Once tek adresi GET ile bildirip anahtari tanitiyoruz, sonra toplu gonderim.
    isinma = (
        f"https://www.bing.com/indexnow?url={urllib.request.quote(SITE + '/', safe='')}"
        f"&key={INDEXNOW_ANAHTAR}"
    )
    try:
        urllib.request.urlopen(isinma, timeout=25).read()
    except Exception:
        pass

    print(f"{len(adresler)} adres bildiriliyor "
          f"(anahtar dosyası: /{INDEXNOW_ANAHTAR}.txt)")
    for sunucu in INDEXNOW_SUNUCULARI:
        kod, d = _istek(sunucu, "POST", govde)
        durum = {200: "kabul edildi", 202: "kuyruğa alındı",
                 400: "hatalı istek", 403: "anahtar doğrulanamadı",
                 422: "adresler alan adıyla uyuşmuyor",
                 429: "çok fazla istek"}.get(kod, f"HTTP {kod}")
        print(f"   {sunucu:44} {durum}")
    print("\n   Not: anahtar dosyası yayımlanmadan (siteye deploy edilmeden) "
          "403 döner; deploy sonrası tekrar çalıştırın.")
    return 0


def durum() -> int:
    tok = belirtec()
    kod, d = _istek("https://www.googleapis.com/webmasters/v3/sites", tok=tok)
    print("Search Console'daki siteler:")
    for s in d.get("siteEntry", []):
        isaret = "  <-- bu site" if ALAN in s["siteUrl"] else ""
        print(f"   {s['permissionLevel']:14} {s['siteUrl']}{isaret}")
    for hedef in (f"sc-domain:{ALAN}", SITE + "/"):
        h = urllib.request.quote(hedef, safe="")
        kod, d = _istek(
            f"https://www.googleapis.com/webmasters/v3/sites/{h}/sitemaps", tok=tok
        )
        if kod == 200:
            for sm in d.get("sitemap", []):
                print(f"\n   {hedef} site haritası:")
                print(f"     {sm.get('path')}")
                print(f"     son indirme: {sm.get('lastDownloaded', 'henüz yok')}")
                print(f"     uyarı: {sm.get('warnings', 0)}  hata: {sm.get('errors', 0)}")
    return 0


if __name__ == "__main__":
    komut = sys.argv[1] if len(sys.argv) > 1 else "durum"
    raise SystemExit(
        {"dogrula": dogrula, "sitemap": sitemap_gonder,
         "indexnow": indexnow, "durum": durum}[komut]()
    )
