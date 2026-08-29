# Kamu Misafirhaneleri

**kamumisfirhaneleri.com** — Türkiye'nin 81 ilindeki kamu konaklama tesislerinin dizini:
öğretmenevi, polisevi, bakanlık misafirhanesi ve üniversite sosyal tesisleri.

Statik site. Tesisler HTML'e basılır (arama motorları ve JavaScript'siz tarayıcılar için),
JavaScript yalnızca filtreleme yapar.

## Veri nereden geliyor

| Alan | Kaynak |
|---|---|
| Öğretmenevi adı, il, ilçe, telefon | [MEB Destek Hizmetleri öğretmenevi listesi](https://dhgm.meb.gov.tr/edestek/ogretmenevi/ogretmenevi_liste.aspx) |
| Polisevi, bakanlık ve üniversite tesisleri | Kurumun kendi `.gov.tr` / `.edu.tr` sayfası — her kayıtta `kaynak` alanı var |
| 2026 fiyatları | Tesisin kendi yayımladığı fiyat listesi — kartta kaynak bağlantısıyla |
| Ankara mesafesi | Bilinen karayolu mesafelerinden yaklaşık hesap, ölçülmüş değil |

Hiçbir e-posta, telefon veya fiyat tahminle yazılmadı. Bulunamayan alan boş bırakıldı.

## Dosyalar

```
index.html      tüm site (tesisler gömülü)
tesisler.json   ham veri, /tesisler.json adresinden CORS ile açık
Dockerfile      nginx:alpine
nginx.conf      gzip, önbellek başlıkları, güvenlik başlıkları
```

## Veriyi güncelleme

Kaynak betikler `scratchpad` klasöründe:

```
tesis_topla.py        MEB listesini çeker    -> tesisler.json
tesis_zenginlestir.py doğrulanmış kayıtları ekler
tesis_ek2.py          ikinci tur kayıtlar + Ankara mesafeleri
site_uret.py          tesisler.json -> bu klasör
```

## Yayın

Coolify üzerinden Dockerfile ile derlenir ve `kamumisfirhaneleri.com` alan adına bağlanır.
`main` dalına push yeterlidir.

## Uyarı

Bağımsız bir dizindir; hiçbir kuruma ait değildir, rezervasyon almaz.
Fiyat ve koşullar kurumlar tarafından değiştirilebilir.
