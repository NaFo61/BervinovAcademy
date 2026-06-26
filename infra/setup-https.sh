#!/usr/bin/env bash
# HTTPS на сервере.
#
# Вариант 1 — только IP (самоподписанный, браузер предупредит):
#   sudo ./infra/setup-https.sh
#
# Вариант 2 — домен (Let's Encrypt, без предупреждений):
#   sudo ./infra/setup-https.sh academy.example.com
#
set -euo pipefail

DOMAIN="${1:-}"
SSL_DIR="/etc/nginx/ssl"
GATEWAY="/etc/nginx/sites-available/gateway.conf"
REPO_GATEWAY="$(cd "$(dirname "$0")" && pwd)/nginx-gateway.conf"

if [[ "${EUID:-}" -ne 0 ]]; then
  echo "Запусти от root: sudo $0 [домен]"
  exit 1
fi

apt-get update -qq
apt-get install -y -qq nginx openssl

mkdir -p "$SSL_DIR" /var/www/certbot

if [[ -n "$DOMAIN" ]]; then
  apt-get install -y -qq certbot python3-certbot-nginx
  cp "$REPO_GATEWAY" "$GATEWAY"
  sed -i 's/\r$//' "$GATEWAY"
  nginx -t && systemctl reload nginx
  certbot --nginx -d "$DOMAIN" --non-interactive --agree-tos --register-unsafely-without-email --redirect
  echo "Готово: https://${DOMAIN}/academy/"
else
  openssl req -x509 -nodes -days 825 -newkey rsa:2048 \
    -keyout "$SSL_DIR/server.key" \
    -out "$SSL_DIR/server.crt" \
    -subj "/CN=161.104.46.236" \
    -addext "subjectAltName=IP:161.104.46.236,DNS:localhost"
  chmod 600 "$SSL_DIR/server.key"
  cp "$REPO_GATEWAY" "$GATEWAY"
  sed -i 's/\r$//' "$GATEWAY"
  nginx -t && systemctl reload nginx
  echo "Готово (самоподписанный): https://161.104.46.236/academy/"
  echo "Браузер покажет предупреждение — это нормально для IP без домена."
  echo "Для нормального HTTPS: sudo $0 ваш-домен.ru"
fi
