# Деплой Bervinov Academy на сервер

На сервере только эта папка (без исходников):

```
/opt/bervinov-academy/
├── docker-compose.yml
├── .env
├── restart.sh
└── full-restart.sh
```

Образы: Docker Hub `bervinov-academy-*` (собираются в CI).

```bash
./restart.sh
```

Host nginx: `deploy/nginx-snippet.conf` — upstream `bervinov-academy`.
