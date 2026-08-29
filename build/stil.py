"""CSS küçültme, karma adlandırma ve kritik stil.

İki şey yapar:
  1. `static/s.css` küçültülüp `static/s.<karma>.css` olarak yazılır. Karma adı
     sayesinde dosya "immutable" önbelleğe alınabilir; içerik değişince ad değişir.
  2. İlk ekranı boyayan kurallar (`KRITIK`) sayfaya gömülür. Böylece tarayıcı
     boyamak için ağdan CSS beklemez; tam stil arkadan, engellemeden yüklenir.

Kritik blok elle tutulur ve bilinçli olarak küçüktür: yalnızca üst bar, kahraman
alanı, kırıntı ve tesis sayfasının başlık bloğu. Geri kalan her şey (araçlar,
harita, alt bilgi) ilk ekranda görünmüyor.
"""

from __future__ import annotations

import hashlib
import re
from pathlib import Path

KOK = Path(__file__).resolve().parent.parent


def kucult(css: str) -> str:
    """Güvenli CSS küçültme.

    İki nokta üst üste etrafındaki boşluğa DOKUNULMAZ. Daha önce dokunuyordu ve
    medya sorgularını korumak için eklenen `not(` -> `not (` düzeltmesi
    `.gez:not([data-acik])` seçicisini de bozup kuralı geçersiz kılmıştı;
    mobil menü hiç kapanmıyordu. Kazanç birkaç yüz bayt, risk buydu.
    """
    css = re.sub(r"/\*.*?\*/", "", css, flags=re.S)
    css = re.sub(r"\s+", " ", css)
    css = re.sub(r"\s*([{};,>~])\s*", r"\1", css)
    css = re.sub(r";}", "}", css)
    css = css.replace("@media(", "@media (")
    return css.strip()


def _kural_sayisi(css: str) -> int:
    return css.count("{")


def yayimla(cikti_kok: Path) -> str:
    """s.css'i küçültüp karma adıyla yazar, sayfada kullanılacak yolu döndürür."""
    ham = (KOK / "static" / "s.css").read_text("utf-8")
    kucuk = kucult(ham)
    # Küçültme hiçbir kuralı düşürmemeli
    once, sonra = _kural_sayisi(re.sub(r"/\*.*?\*/", "", ham, flags=re.S)), _kural_sayisi(kucuk)
    if once != sonra:
        raise SystemExit(f"CSS küçültme {once - sonra} kural kaybetti — durduruldu")
    for zorunlu in (".gez:not([data-acik])", "@media (max-width:1000px)",
                    ".gez-dg", "size-adjust"):
        if zorunlu not in kucuk:
            raise SystemExit(f"CSS küçültme sonrası kayıp: {zorunlu}")
    karma = hashlib.sha256(kucuk.encode("utf-8")).hexdigest()[:10]
    ad = f"s.{karma}.css"
    hedef = cikti_kok / "static"
    hedef.mkdir(parents=True, exist_ok=True)
    (hedef / ad).write_text(kucuk, "utf-8")
    return f"/static/{ad}"


# İlk ekranı boyayan kurallar. Yazı tipi tanımları burada değil; `swap` sayesinde
# metin yedek yazı tipiyle hemen görünür, asıl yazı tipi tam stille birlikte gelir.
_KRITIK_HAM = """
@font-face{font-family:"Newsreader Yedek";src:local("Georgia"),local("Times New Roman");
size-adjust:88%;font-weight:400 700;font-style:normal}
@font-face{font-family:"Inter Yedek";src:local("Arial"),local("Helvetica Neue"),local("Liberation Sans");
size-adjust:107%;font-weight:400 700;font-style:normal}
:root{--kagit:#FBF9F5;--yuzey:#FFF;--yuzey2:#F4F1E9;--yuzey3:#EDE9DE;--cizgi:#E3DED2;
--cizgi2:#D2CBBB;--murekkep:#16201E;--orta:#3E4B48;--soluk:#5E6B67;--vurgu:#0D5C4E;
--vurgu-koyu:#08453A;--vurgu-yumusak:#E2F0EB;--vurgu-cizgi:#B9DBD0;--deniz:#0B6580;
--deniz-yumusak:#E1EFF4;--altin:#8F5A15;--altin-yumusak:#F7EEDF;--r:14px;--r-sm:10px;
--en:1180px;--sans:Inter,"Inter Yedek",system-ui,-apple-system,"Segoe UI",Roboto,sans-serif;
--serif:Newsreader,"Newsreader Yedek",Georgia,"Times New Roman",serif;
--golge-sm:0 1px 2px rgba(20,30,28,.06),0 1px 3px rgba(20,30,28,.04)}
@media (prefers-color-scheme:dark){:root:not([data-tema="acik"]){--kagit:#0F1413;
--yuzey:#171E1C;--yuzey2:#1E2624;--yuzey3:#252E2C;--cizgi:#2B3532;--cizgi2:#3A4643;
--murekkep:#EBF0EE;--orta:#C0CCC9;--soluk:#93A19D;--vurgu:#4FD3AF;--vurgu-koyu:#7FE3C6;
--vurgu-yumusak:#14302A;--vurgu-cizgi:#1F473E;--deniz:#5CC2E0;--deniz-yumusak:#122C36;
--altin:#E0A85C;--altin-yumusak:#312415;--golge-sm:0 1px 2px rgba(0,0,0,.4)}}
*,*::before,*::after{box-sizing:border-box}
html{-webkit-text-size-adjust:100%}
body{margin:0;background:var(--kagit);color:var(--murekkep);font-family:var(--sans);
font-size:16px;line-height:1.6;-webkit-font-smoothing:antialiased}
img{max-width:100%;display:block}
a{color:var(--vurgu)}
h1,h2,h3{font-family:var(--serif);font-weight:600;line-height:1.16;letter-spacing:-.012em;margin:0}
h1{font-size:clamp(2rem,1.35rem + 2.6vw,3.15rem)}
p{margin:0 0 1em}
.kap{max-width:var(--en);margin-inline:auto;padding-inline:20px}
.atla{position:absolute;left:-9999px;top:0}
.ik{width:1.15em;height:1.15em;flex:none;stroke:currentColor;fill:none;stroke-width:1.7;
stroke-linecap:round;stroke-linejoin:round;vertical-align:-.16em}
.ust{position:sticky;top:0;z-index:40;background:var(--kagit);border-bottom:1px solid var(--cizgi)}
.ust .kap{display:flex;align-items:center;gap:8px;height:62px;position:relative}
.marka{display:flex;align-items:center;gap:10px;font-family:var(--serif);font-size:1.16rem;
font-weight:600;color:var(--murekkep);text-decoration:none;margin-right:auto}
.marka svg{width:28px;height:28px;flex:none}
.marka span{color:var(--soluk);font-weight:500}
.gez{display:flex;gap:2px;align-items:center}
.gez a{padding:8px 13px;border-radius:99px;font-size:.925rem;font-weight:500;
color:var(--orta);text-decoration:none;white-space:nowrap}
.gez-dg{display:none;align-items:center;gap:9px;margin-left:auto;height:40px;padding:0 14px;
background:var(--yuzey);border:1.5px solid var(--cizgi2);border-radius:99px;font:inherit;
font-size:.9rem;font-weight:600;color:var(--murekkep);cursor:pointer}
.gez-cizgi{position:relative;width:16px;height:2px;border-radius:2px;background:currentColor}
.gez-cizgi::before,.gez-cizgi::after{content:"";position:absolute;left:0;width:16px;height:2px;
border-radius:2px;background:currentColor}
.gez-cizgi::before{translate:0 -5px}
.gez-cizgi::after{translate:0 5px}
@media (max-width:1000px){.gez-dg{display:inline-flex}
.gez{position:absolute;top:calc(100% + 9px);right:20px;flex-direction:column;align-items:stretch;
min-width:min(248px,calc(100vw - 40px));padding:8px;background:var(--yuzey);
border:1px solid var(--cizgi);border-radius:var(--r)}
.gez:not([data-acik]){display:none}}
@media (max-width:700px){.ust .kap{height:56px}.marka span{display:none}}
.krnt{font-size:.83rem;color:var(--soluk);padding:14px 0 0;display:flex;flex-wrap:wrap;
gap:6px;align-items:center}
.krnt a{color:var(--soluk);text-decoration:none}
.kahraman{padding-block:clamp(38px,7vw,76px) clamp(30px,4vw,46px);position:relative;overflow:hidden}
.kahraman h1{max-width:16ch;text-wrap:balance}
.kahraman h1 em{font-style:normal;color:var(--vurgu)}
.giris{font-size:clamp(1.02rem,.97rem + .3vw,1.19rem);color:var(--orta);max-width:56ch;
margin:16px 0 0;line-height:1.55}
.ara{position:relative;margin-top:26px;max-width:560px}
.ara input{width:100%;height:56px;padding:0 52px 0 48px;font:inherit;font-size:1.02rem;
background:var(--yuzey);color:var(--murekkep);border:1.5px solid var(--cizgi2);
border-radius:var(--r);box-shadow:var(--golge-sm)}
.ara .ik-ara{position:absolute;left:17px;top:50%;translate:0 -50%;width:19px;height:19px;
color:var(--soluk)}
.sayilar{display:flex;flex-wrap:wrap;gap:10px;margin-top:24px;padding:0;list-style:none}
.sayilar li{display:flex;align-items:baseline;gap:7px;background:var(--yuzey);
border:1px solid var(--cizgi);border-radius:99px;padding:7px 15px;font-size:.87rem;color:var(--soluk)}
.sayilar b{font-size:1.02rem;font-weight:700;color:var(--murekkep)}
.rz{display:inline-flex;align-items:center;gap:5px;padding:3px 10px;border-radius:99px;
font-size:.775rem;font-weight:600;line-height:1.5;white-space:nowrap}
.ts-ust{position:relative;height:clamp(300px,42vw,420px);display:flex;align-items:flex-end;
overflow:hidden;background:var(--yuzey3)}
.ts-ust>img{position:absolute;inset:0;width:100%;height:100%;object-fit:cover}
.ts-ust::after{content:"";position:absolute;inset:0;
background:linear-gradient(180deg,rgba(8,20,18,.42) 0%,rgba(8,20,18,.22) 38%,rgba(8,20,18,.84) 100%)}
.ts-ust .kap{position:relative;z-index:2;padding-block:26px;color:#fff;width:100%}
.ts-ust h1{color:#fff;max-width:22ch;display:-webkit-box;-webkit-line-clamp:3;
-webkit-box-orient:vertical;overflow:hidden}
.ts-ust .rzs{display:flex;flex-wrap:wrap;gap:7px;margin-bottom:13px}
.ts-ust .rz{background:rgba(255,255,255,.93);color:var(--orta)}
.ts-ust .yer{margin:11px 0 0;font-size:1rem;opacity:.94;display:flex;align-items:center;gap:7px}
.ozet{font-size:1.06rem;line-height:1.62;color:var(--orta);border-left:3px solid var(--vurgu-cizgi);
padding-left:17px;margin:0 0 26px}
.bl{padding-block:clamp(34px,5vw,60px)}
"""

KRITIK = kucult(_KRITIK_HAM)
