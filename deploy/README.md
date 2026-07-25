# Деплой Bervinov Academy на сервер

На сервере только эта папка (без исходников):

```
/opt/bervinov-academy/
├── docker-compose.yml
├── .env
├── lib.sh
├── ci-deploy.sh
├── restart.sh
└── full-restart.sh
```

Образы: Docker Hub `bervinov-academy-*` (собираются в CI).

CI вызывает `./ci-deploy.sh` (pull с ретраями, health внутри сессии, timeout 30m).
Вручную:

```bash
./restart.sh
```

Host nginx: `deploy/nginx-snippet.conf` — upstream `bervinov-academy`.
