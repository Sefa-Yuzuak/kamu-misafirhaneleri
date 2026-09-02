# 1) Siteyi üret
FROM python:3.12-slim AS derleyici
WORKDIR /src
# Tek dış bağımlılık: yazı tipi alt kümeleme (build/yazitipi.py). Kurulu
# değilse derleme çalışır ama latin-ext dosyaları tam boy kalır ve sayfa
# başına ~150 KB fazladan iner — bu yüzden imaja kuruluyor.
RUN pip install --no-cache-dir fonttools==4.* brotli
COPY build/ build/
COPY static/ static/
COPY img/ img/
COPY data/ data/
COPY tesisler.json favicon.svg ./
RUN python build/derle.py

# 2) Yayınla
FROM nginx:alpine
COPY nginx.conf /etc/nginx/conf.d/default.conf
COPY --from=derleyici /src/site /usr/share/nginx/html
EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]
