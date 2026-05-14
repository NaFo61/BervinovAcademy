#!/usr/bin/env python3
"""
Собирает project_prompt.txt — контекст репозитория для LLM/нейросетей.

Запуск из корня репозитория:
  python scripts/generate-prompt.py
"""

from __future__ import annotations

import json
import os
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SCRIPTS_DIR = ROOT / "scripts"
OUTPUT_FILE = SCRIPTS_DIR / "project_prompt.txt"

# Директории не показывать в дереве (шум и размер)
EXCLUDE_DIRS = {
    "__pycache__",
    ".git",
    ".venv",
    "venv",
    "node_modules",
    "dist",
    "build",
    ".pytest_cache",
    ".mypy_cache",
    ".ruff_cache",
    ".cursor",
    "coverage",
    "static",
    "media",
    "wheels",
    "htmlcov",
}

# Расширения → метка типа (без emoji в заголовках секций — лучше для совместимости)
EXT_LABEL = {
    ".py": "[py]",
    ".ts": "[ts]",
    ".tsx": "[tsx]",
    ".js": "[js]",
    ".jsx": "[jsx]",
    ".json": "[json]",
    ".yml": "[yml]",
    ".yaml": "[yml]",
    ".html": "[html]",
    ".css": "[css]",
    ".md": "[md]",
    ".txt": "[txt]",
    ".toml": "[toml]",
    ".sh": "[sh]",
    ".bat": "[bat]",
}


def read_text(path: Path, max_lines: int | None = None) -> str:
    try:
        text = path.read_text(encoding="utf-8")
    except OSError:
        return "[не удалось прочитать файл]"
    if max_lines is None:
        return text
    lines = text.splitlines()
    head = "\n".join(lines[:max_lines])
    if len(lines) > max_lines:
        head += f"\n... ({len(lines) - max_lines} строк не показано)"
    return head


def load_pyproject_version() -> str:
    path = ROOT / "pyproject.toml"
    if not path.is_file():
        return "unknown"
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.strip().startswith("version"):
            m = re.match(r'\s*version\s*=\s*["\']([^"\']+)["\']', line)
            if m:
                return m.group(1)
    return "unknown"


def tree_lines(directory: Path, max_depth: int = 3, depth: int = 0) -> list[str]:
    out: list[str] = []
    if depth > max_depth:
        return out
    indent = "  " * depth
    try:
        entries = sorted(directory.iterdir(), key=lambda p: (not p.is_dir(), p.name.lower()))
    except OSError:
        return out
    dirs = [e for e in entries if e.is_dir() and e.name not in EXCLUDE_DIRS and not e.name.startswith(".")]
    files = [e for e in entries if e.is_file() and not e.name.startswith(".")]
    for d in dirs:
        out.append(f"{indent}{d.name}/")
        out.extend(tree_lines(d, max_depth, depth + 1))
    for f in files:
        ext = f.suffix.lower()
        tag = EXT_LABEL.get(ext, "[file]")
        out.append(f"{indent}{tag} {f.name}")
    return out


def limited_tree(root: Path, max_depth: int = 3, max_lines: int = 220) -> list[str]:
    lines = tree_lines(root, max_depth=max_depth)
    if len(lines) <= max_lines:
        return lines
    return lines[:max_lines] + [f"... ({len(lines) - max_lines} строк дерева скрыто; увеличьте max_lines в скрипте)"]


def django_apps_summary() -> list[str]:
    backend = ROOT / "backend"
    if not backend.is_dir():
        return ["  (папка backend не найдена)"]
    rows = []
    for p in sorted(backend.iterdir()):
        if not p.is_dir() or p.name.startswith("_"):
            continue
        apps_py = p / "apps.py"
        if not apps_py.is_file():
            continue
        parts = []
        if (p / "models.py").is_file():
            parts.append("models")
        if (p / "views.py").is_file():
            parts.append("views")
        if (p / "viewsets.py").is_file():
            parts.append("viewsets")
        if (p / "serializers.py").is_file():
            parts.append("serializers")
        if (p / "urls.py").is_file():
            parts.append("urls")
        hint = ", ".join(parts) if parts else "конфиг/утилиты"
        rows.append(f"  • {p.name}: {hint}")
    return rows or ["  (приложений с apps.py не найдено)"]


def extract_frontend_routes() -> list[str]:
    route_tree = ROOT / "frontend" / "src" / "routeTree.gen.ts"
    if not route_tree.is_file():
        return ["  (frontend/src/routeTree.gen.ts не найден — соберите роутер TanStack)"]
    text = route_tree.read_text(encoding="utf-8")
    # Интерфейс FileRoutesByFullPath: строки вида "  '/about': typeof AboutRoute"
    m = re.search(r"interface FileRoutesByFullPath\s*\{([^}]+)\}", text, re.DOTALL)
    body = m.group(1) if m else text
    paths = re.findall(r"^\s*'([^']*)'\s*:", body, re.MULTILINE)
    if not paths:
        paths = re.findall(r"path:\s*['\"]([^'\"]+)['\"]", text)
    uniq: list[str] = []
    seen: set[str] = set()
    for p in paths:
        display = "/" if p == "" else (p if p.startswith("/") else f"/{p}")
        if display not in seen:
            seen.add(display)
            uniq.append(display)
    return [f"  • {p}" for p in uniq] if uniq else ["  (см. frontend/src/routes/)"]


def snippet_block(title: str, path: Path, desc: str, max_lines: int = 45) -> list[str]:
    try:
        rel = path.relative_to(ROOT)
    except ValueError:
        rel = path
    block = [
        "",
        f"  [{title}] {rel}",
        f"  ({desc})",
        "  --- начало файла ---",
    ]
    for line in read_text(path, max_lines=max_lines).splitlines():
        block.append(f"  | {line}")
    block.append("  --- конец файла ---")
    return block


def npm_scripts_and_deps() -> tuple[list[str], list[str]]:
    pkg = ROOT / "frontend" / "package.json"
    if not pkg.is_file():
        return [], []
    try:
        data = json.loads(pkg.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return [], []
    scripts = [f"  npm run {k}" for k in sorted((data.get("scripts") or {}).keys())]
    deps = sorted((data.get("dependencies") or {}).keys())
    dev = sorted((data.get("devDependencies") or {}).keys())
    lines = []
    if deps:
        lines.append("  dependencies (основное):")
        for d in deps:
            lines.append(f"    - {d}")
    if dev:
        lines.append("  devDependencies:")
        for d in dev:
            lines.append(f"    - {d}")
    return scripts, lines


def requirements_head(max_lines: int = 35) -> list[str]:
    req = ROOT / "requirements.txt"
    if not req.is_file():
        return ["  (requirements.txt не найден)"]
    lines = []
    for line in read_text(req, max_lines=max_lines).splitlines():
        lines.append(f"  | {line}")
    return lines


def main() -> int:
    os.chdir(ROOT)
    lines: list[str] = []

    version = load_pyproject_version()
    now = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

    # --- Мета: как трактовать документ для любой модели ---
    lines += [
        "=" * 80,
        "КОНТЕКСТ РЕПОЗИТОРИЯ (автогенерация для LLM)",
        "Bervinov Academy",
        "=" * 80,
        "",
        "## ДЛЯ МОДЕЛИ (как использовать этот файл)",
        "",
        "  • Назначение: одноразовый снимок структуры и ключевых точек входа; не замена чтению кода.",
        "  • Источник истины: файлы в репозитории; при конфликте доверять коду, не этому тексту.",
        "  • Языки: интерфейс и комментарии часто на русском; имена в коде и API — латиница.",
        "  • Репозиторий: монолит — `backend/` (Django), `frontend/` (React + Vite), `nginx/` (прокси в Docker).",
        "  • Обновление: перегенерировать командой `python scripts/generate-prompt.py`.",
        "",
        "## ОБЗОР ПРОЕКТА",
        "",
        f"  Название: Bervinov Academy",
        f"  Версия (pyproject): {version}",
        "  Описание: образовательная платформа (курсы, уроки, менторство, прогресс, подписки); бэкенд REST на Django.",
        "  Тип: fullstack — Django REST + SPA на React.",
        f"  Сгенерировано (UTC): {now}",
        "",
        "## КАК СВЯЗАНЫ ЧАСТИ (поток запросов)",
        "",
        "  Разработка (локально):",
        "    1) Backend: `python manage.py runserver` из каталога `backend/` (порт 8000 по умолчанию).",
        "    2) Frontend: `npm run dev` в `frontend/` — Vite на порту 3000; в `vite.config` прокси `/api` → backend.",
        "",
        "  Production (Docker / nginx):",
        "    Браузер → nginx (порт 80) → статика SPA из `/`; пути `/api/`, `/admin/`, `/static/`, `/media/` проксируются на контейнер backend.",
        "",
        "  Схема (упрощённо):",
        "    [клиент] --HTTP--> [nginx или Vite dev] --/api--> [Django DRF]",
        "",
        "## ТОЧКИ ВХОДА BACKEND",
        "",
        "  • Корневые URL: `backend/school_platform/urls.py` — монтирует `api/` → приложения users, content, progress;",
        "    также admin, health, drf-spectacular (swagger/redoc).",
        "  • Настройки: `backend/school_platform/settings.py`.",
        "  • ASGI/WSGI: `asgi.py`, `wsgi.py`; Celery: `celery.py`.",
        "",
        "## FRONTEND (маршруты SPA)",
        "",
        "  Файловый роутинг TanStack Router; сгенерированное дерево: `frontend/src/routeTree.gen.ts`.",
        "  Пути страниц:",
    ]
    lines.extend(extract_frontend_routes())
    lines.append("")
    npm_scripts, dep_lines = npm_scripts_and_deps()
    if npm_scripts:
        lines.append("  Скрипты package.json:")
        lines.extend(npm_scripts)
        lines.append("")
    lines.append("## СТЕК (кратко)")
    lines.append("")
    lines.append("  Backend: Python 3.11+, Django, DRF, JWT (simplejwt), Celery, Redis, PostgreSQL.")
    lines.append("  Frontend: React 18, TypeScript, Vite, TanStack Router, Tailwind v4 (@tailwindcss/vite), axios.")
    if dep_lines:
        lines.extend(dep_lines)
    lines.append("")
    lines.append("  Фрагмент requirements.txt:")
    lines.extend(requirements_head())
    lines.append("")
    lines.append("## DJANGO-ПРИЛОЖЕНИЯ (папки в backend/ с apps.py)")
    lines.append("")
    lines.extend(django_apps_summary())
    lines.append("")
    lines.append("## ДЕРЕВО РЕПОЗИТОРИЯ (укороченное)")
    lines.append("")
    lines.extend(f"  {ln}" for ln in limited_tree(ROOT, max_depth=3))
    lines.append("")

    key_files: list[tuple[str, Path, str, int]] = [
        ("docker-compose", ROOT / "docker-compose.yml", "оркестрация сервисов", 55),
        ("nginx", ROOT / "nginx" / "nginx.conf", "прокси SPA и API", 85),
        ("django urls", ROOT / "backend" / "school_platform" / "urls.py", "корневые маршруты Django", 55),
        ("vite", ROOT / "frontend" / "vite.config.js", "dev-сервер и proxy /api", 35),
        ("README", ROOT / "README.md", "человеческое описание проекта", 40),
        ("pyproject", ROOT / "pyproject.toml", "метаданные Python-проекта", 35),
        ("env example", ROOT / ".env.example", "переменные окружения (шаблон)", 35),
    ]
    lines.append("## ФРАГМЕНТЫ КЛЮЧЕВЫХ ФАЙЛОВ")
    for title, path, desc, mx in key_files:
        if path.is_file():
            lines.extend(snippet_block(title, path, desc, max_lines=mx))
        else:
            lines.append("")
            lines.append(f"  [{title}] пропущено — нет файла: {path}")

    dc = ROOT / "docker-compose.yml"
    lines.append("")
    lines.append("## DOCKER COMPOSE (полный текст, если уместен)")
    lines.append("")
    if dc.is_file():
        for line in read_text(dc, max_lines=200).splitlines():
            lines.append(f"  {line}")
    else:
        lines.append("  (docker-compose.yml не найден)")

    lines.append("")
    lines.append("=" * 80)
    lines.append("КОНЕЦ ФАЙЛА КОНТЕКСТА")
    lines.append("=" * 80)

    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_FILE.write_text("\n".join(lines), encoding="utf-8")
    print(f"OK: записано {OUTPUT_FILE.relative_to(ROOT)} ({len(lines)} строк)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
