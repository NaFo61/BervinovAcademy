#!/bin/sh
set -e
cd /app/backend
python manage.py compilemessages -l en 2>/dev/null || true
if [ "${SKIP_MIGRATE:-0}" != "1" ]; then
  python manage.py migrate --noinput
fi
if [ "${SKIP_COLLECTSTATIC:-0}" != "1" ]; then
  python manage.py collectstatic --noinput
fi
exec "$@"
