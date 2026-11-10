"""Database access and GET filters for the bank catalog."""

from __future__ import annotations

import re
import sqlite3
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
DB_PATH = BASE_DIR / "bank_catalog.db"
SCHEMA_PATH = BASE_DIR / "schema.sql"


def _py_lower(value: object) -> object:
    """Unicode-aware lower for SQLite LIKE (built-in lower() ignores Cyrillic)."""
    if value is None:
        return None
    return str(value).lower()


def get_db() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    conn.create_function("py_lower", 1, _py_lower)
    return conn


def init_db() -> None:
    """Create tables and seed data if the database file is missing or empty."""
    if DB_PATH.exists() and DB_PATH.stat().st_size > 0:
        with get_db() as conn:
            row = conn.execute("SELECT COUNT(*) AS c FROM products").fetchone()
            if row and row["c"] > 0:
                return

    with get_db() as conn:
        conn.executescript(SCHEMA_PATH.read_text(encoding="utf-8"))


def all_audiences() -> list[sqlite3.Row]:
    with get_db() as conn:
        return conn.execute(
            "SELECT id, name FROM audiences ORDER BY name"
        ).fetchall()


def like_pattern(text: str) -> str:
    """Escape LIKE wildcards so user input is treated as literal text."""
    text = text.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")
    return f"%{text}%"


def filtered_products(args: dict) -> list[sqlite3.Row]:
    """
    Catalog with JOIN to audiences.
    Filters come from GET and are combined with AND.
    clearFilter skips every condition.
    """
    sql = """
        SELECT
            p.id,
            p.img_path,
            p.name,
            p.description,
            p.tariff_cost,
            p.audience_id,
            a.name AS audience_name
        FROM products p
        INNER JOIN audiences a ON p.audience_id = a.id
    """
    where: list[str] = []
    binds: list[object] = []

    if "clearFilter" not in args:
        name = (args.get("name") or "").strip()
        if name:
            # py_lower: same case-insensitive feel as MySQL utf8mb4_unicode_ci
            where.append("py_lower(p.name) LIKE ? ESCAPE '\\'")
            binds.append(like_pattern(name.lower()))

        audience_id = args.get("audience_id") or ""
        if str(audience_id).isdigit():
            where.append("p.audience_id = ?")
            binds.append(int(audience_id))

        description = (args.get("description") or "").strip()
        if description:
            where.append("py_lower(p.description) LIKE ? ESCAPE '\\'")
            binds.append(like_pattern(description.lower()))

        cost = (args.get("tariff_cost") or "").strip()
        if cost.isdigit():
            where.append("p.tariff_cost = ?")
            binds.append(int(cost))

    if where:
        sql += " WHERE " + " AND ".join(where)

    sql += " ORDER BY p.name"

    with get_db() as conn:
        return conn.execute(sql, binds).fetchall()


def is_safe_image_name(name: str) -> bool:
    return bool(re.fullmatch(r"[A-Za-z0-9._-]+", name or ""))
