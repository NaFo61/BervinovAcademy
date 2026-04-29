# Bervinov Academy Frontend

Простой и понятный React + Tailwind фронтенд для проекта Bervinov Academy.

## Установка

```bash
cd frontend
npm install
```

## Локальная разработка

```bash
npm run dev
```

Сервер запустится на `http://localhost:3000`.

## Запуск через Docker

Из корня проекта:

```bash
docker compose up --build
```

После запуска:
- `http://localhost:3000` — frontend
- `http://localhost:8000` — backend

## Как фронтенд общается с backend

В `src/App.jsx` используется Axios:
- `import.meta.env.VITE_API_PROXY` берёт адрес из Docker Compose
- запрос идёт на `/api/content/courses/`
- данные курса рендерятся списком

## Как писать удобно

1. **Новые страницы и компоненты**
   - создавай `src/components/` и `src/pages/`
   - импортируй `App.jsx` и используй `className` с Tailwind

2. **Tailwind**
   - классы используют BEM-подобную семантику: `bg-slate-900`, `rounded-3xl`, `text-slate-100`
   - сохраняй минимальный рендер и добавляй только полезные блоки

3. **Запросы к API**
   - используй `axios.get('/api/content/courses/')`
   - ошибки сразу показываются в UI
   - cообщение о загрузке видно, пока данные приходят

## Главные файлы

- `src/main.jsx` — точка входа
- `src/App.jsx` — загрузка курсов и интерфейс
- `src/index.css` — Tailwind + базовые стили
- `vite.config.js` — прокси и dev-сервер
- `frontend/Dockerfile` — контейнер для frontend

## Советы

- Пиши логику по разделам: компонент + хук + API
- Не держи стили отдельно, если можно сделать на Tailwind
- Используй `npm run lint` и `npm run lint:fix`
- Если добавляешь новые API, создавай отдельный файл, например `src/api/courses.js`
