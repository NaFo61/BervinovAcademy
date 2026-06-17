# Сборка dist — только копирование статики (см. build-dist.mjs).
# Node не нужен: меньше образов с Docker Hub и быстрее старт.
FROM alpine:3.20

WORKDIR /app

COPY . .

RUN rm -rf dist && mkdir -p dist \
    && cp index.html dist/ \
    && cp -r src dist/ \
    && (test -d public && cp -r public dist/ || true)
