# Selectel S3 для видеоуроков (Pro)

**Статус:** в работе / к деплою

## Зачем

Видео к урокам хранятся в Selectel S3 (не на диске VPS).  
Смотреть могут только Pro — как и раньше. Ссылки на файл **временные** (signed URL).

## Что настроить в Selectel

- Бакет `bervinov-academy-videos`, `ru-6`, стандартный, **приватный**, адресация **vHosted**
- Сервисный пользователь с ролью `s3.user` на проект
- S3 Access Key + Secret Key

## Env на сервере

```
USE_S3=true
AWS_ACCESS_KEY_ID=...
AWS_SECRET_ACCESS_KEY=...
AWS_STORAGE_BUCKET_NAME=bervinov-academy-videos
AWS_S3_ENDPOINT_URL=https://s3.ru-6.storage.selcloud.ru
AWS_S3_REGION_NAME=ru-6
AWS_S3_ADDRESSING_STYLE=path
AWS_QUERYSTRING_AUTH=true
AWS_QUERYSTRING_EXPIRE=3600
```

## Как заливать

Ментор → Редактор контента → урок → вкладка решения/видео → файл MP4.  
Файл уходит в S3 через backend (не напрямую из браузера в бакет).

## Лимиты

- nginx `client_max_body_size` 512m  
- Django `DATA_UPLOAD_MAX_MEMORY_SIZE` 512MB  

На host-nginx тоже проверьте `client_max_body_size` ≥ 512m.
