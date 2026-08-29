# Kamu Misafirhaneleri

**[kamumisafirhaneler.com](https://kamumisafirhaneler.com)** — Türkiye'nin 81 ilindeki
kamu konaklama tesislerinin dizini: öğretmenevi, polisevi, bakanlık misafirhanesi ve
üniversite sosyal tesisleri.

Statik site. 562 tesisin her biri için ayrı sayfa üretilir; JavaScript yalnızca arama
ve harita için kullanılır, içeriğin tamamı HTML'de hazır gelir.

## İlke

**Hiçbir alan tahminle doldurulmaz.** Telefon, e-posta, fiyat ve denize konum yalnızca
kurumun kendi yayınında varsa yazılır; yoksa alan boş bırakılır ve sayfada bunun
bilinmediği açıkça söylenir. Aynı ilke fotoğraflar ve harita için de geçerlidir.

## Sayfa yapısı

```
/                      arama, tesis türleri, kıyı illeri, rehber, 81 il
/ara/                  istemci tarafı arama
/harita/               562 tesis, kümelenmiş harita
/il/                   81 il, alfabetik
/il/<il>/              ilin tesisleri + il haritası + SSS
/tesis/<il>-<ad>/      künye, olanaklar, SSS, harita, iletişim (562 sayfa)
/tur/<tür>/            öğretmenevleri, polisevleri, üniversite, kamu
/deniz/                denize konumu doğrulanmış tesisler
/rehber/<yazı>/        veriye dayalı 5 rehber
/kaynaklar/            kurum amblemleri, fotoğraf lisansları, düzeltme
/tesisler.json         ham veri, CORS açık
/llms.txt              üretken arama motorları için özet
```

## Veri nereden geliyor

| Alan | Kaynak |
|---|---|
| Öğretmenevi adı, il, ilçe, telefon | [MEB Destek Hizmetleri öğretmenevi listesi](https://dhgm.meb.gov.tr/edestek/ogretmenevi/ogretmenevi_liste.aspx) |
| Polisevi, bakanlık ve üniversite tesisleri | Kurumun kendi `.gov.tr` / `.edu.tr` sayfası — her kayıtta `kaynak` alanı |
| 2026 fiyatları | Tesisin kendi yayımladığı fiyat listesi |
| Ankara mesafesi | Bilinen karayolu mesafelerinden yaklaşık hesap, ölçülmüş değil |
| İl fotoğrafları | Wikimedia Commons, serbest lisanslı — yazar ve lisans her sayfada |
| Kurum amblemleri | Kurumun kendi sitesindeki ikon dosyası |
| Koordinatlar | OpenStreetMap Nominatim; bulunamayanda ilçe merkezi, `kesinlik` alanıyla işaretli |

## Tasarım

- **Yazı**: Newsreader (başlık) + Inter (arayüz), kendi sunucumuzdan, `latin` ve
  `latin-ext` alt kümeleri `unicode-range` ile — üçüncü parti istek yok.
- **Renk**: sıcak kâğıt zemin, derin çam yeşili vurgu. Karanlık tema desteklenir.
- **İkonlar**: tek renk (`currentColor`), 24×24 çizgi, satır içi SVG.
- **Kart**: 16:9 görsel → ad → konum → olanak ikonları → iletişim düğmeleri.
- **Birincil eylem**: telefonla arama. Dizinde dönüşüm budur, her kartta ilk sırada.

## Derleme

```
python build/derle.py          tesisler.json + data/ -> site/
```

Yardımcı betikler (bir kez çalışır, çıktıları `data/` ve `img/` altında saklanır):

```
build/gorsel.py    Wikimedia'dan 81 il fotoğrafı  -> img/il/, data/gorseller.json
build/logo2.py     kurum amblemleri               -> img/kurum/, data/kurumlar.json
build/konum.py     Nominatim koordinatları        -> data/konumlar.json
```

## Yayın

Coolify, `main` dalına push ile. `Dockerfile` iki aşamalı: python aşaması siteyi
üretir, nginx aşaması yayımlar. `site/` sürüm kontrolüne girmez.

## Uyarı

Bağımsız bir dizindir; hiçbir kuruma ait değildir, hiçbir kurumu temsil etmez ve
rezervasyon almaz. Fiyat ve koşullar kurumlar tarafından değiştirilebilir.
