# FEATURE: Owner Django Admin + Mentor SPA workspace

Status: **IMPLEMENTED** (2026-07-30)

## Goal

Реальная модель школы:

1. **`/admin` (Django Unfold)** — только владелец (`role=admin`). Крутой, сжатый пульт: статистика, пользователи, роли, Pro, enrollment, курсы на уровне школы.
2. **`/mentor` (SPA)** — единственное рабочее место менторов: контент (курсы/модули/уроки/КР), ученики, проверка, созвоны, выдачи доступа к КР.
3. Владелец выдаёт доступ к **`/mentor`** (роль `mentor`), **не** в Django. Mentors: `is_staff=False`.

## Done in code

- Mentors lose Django staff (`User.save` + migration `0016_demote_mentor_staff`)
- Unfold sidebar: люди/Pro/курсы/enrollment/КР; dashboard KPI расширен
- Editor API: create course/module/exam; ACL только `Course.mentor`
- SPA `/mentor`: вкладка КР (unlock/retake), редактор модулей/курсов без ссылок на Django
- Admin nav link «Школа» → `/admin/`

## Deploy

```bash
# на сервере после pull
cd /opt/bervinov-academy && ./deploy/restart.sh   # или ваш обычный путь
# важно: migrate users.0016
```

Назначь менторов на курсы в `/admin/content/course/` (поле mentor), иначе у ментора пустой список курсов.

## Access matrix

| Роль | `/admin` | `/mentor` | Content editor API |
|------|----------|-----------|--------------------|
| admin | да | да | все курсы |
| mentor | нет | да | свои курсы (`Course.mentor`) + без ментора (claim при создании) |
| student | нет | нет | нет |

## Owner Django Admin (главное только)

Sidebar:

- Dashboard (реальные KPI)
- Пользователи (роль, Pro actions)
- Курсы (список, mentor FK, active) — без глубокого CMS-шума в навигации
- Enrollment
- Plans / Entitlements
- КР overview: ExamAttempt, ExamAccessGrant (ops)

Убрать из повседневной навигации (остаются у superuser через поиск/apps при необходимости, но не в sidebar): сырые уроки по типам, translations, notify, communication детали — либо свернуть в «Система».

Dashboard KPI: users, users 30d, active enrollments, Pro active, courses, exam attempts 7d, submissions 7d, charts.

## Mentor SPA

- Расширить editor: create/rename/reorder modules; показать exams; create course (title, tech, assign self as mentor).
- Exam unlock/retake UI (existing API).
- Mentors never redirected to `/admin`.

## Backend changes

- `User.save`: mentor → `is_staff=False`, `is_superuser=False`; admin → staff+superuser.
- Data migration / management: снять `is_staff` у существующих mentors.
- Editor ACL: `user_can_edit_course` — admin или `course.mentor_id == user.id`.
- Module CRUD endpoints under editor API.
- Course create for mentors.
- Clone course includes exams (admin action fix).

## Out of scope

- Payment for Pro
- Separate `/staff` SPA (не нужен — роль `/admin`)
- Drag-and-drop wow / WYSIWYG
- Certificates

## Deploy

Migration + restart. Mentors lose Django login — expected.
`)
