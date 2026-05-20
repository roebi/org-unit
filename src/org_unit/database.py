"""
database.py - SQLite connection lifecycle and shared helpers.

All side effects (DB file, timestamps) are isolated here so tests can
inject an in-memory DB and monkeypatch utcnow_str().
"""
from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from typing import AsyncGenerator

import aiosqlite

DB_PATH: Path = Path("/app/data/org-unit.db")

SENTINEL_DATE = "9999-12-31"

# ---------------------------------------------------------------------------
# DDL
# ---------------------------------------------------------------------------

_DDL = """
PRAGMA journal_mode=WAL;
PRAGMA foreign_keys=ON;

CREATE TABLE IF NOT EXISTS org_unit (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    name            TEXT    NOT NULL,
    description     TEXT,
    parent_id       INTEGER REFERENCES org_unit(id),
    sort_order      INTEGER NOT NULL DEFAULT 0,
    valid_from      TEXT    NOT NULL,
    valid_until     TEXT    NOT NULL DEFAULT '9999-12-31',
    updated_at      TEXT    NOT NULL,
    mutation_reason TEXT    NOT NULL
);

CREATE TABLE IF NOT EXISTS person (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    first_name      TEXT    NOT NULL,
    last_name       TEXT    NOT NULL,
    email           TEXT,
    notes           TEXT,
    valid_from      TEXT    NOT NULL,
    valid_until     TEXT    NOT NULL DEFAULT '9999-12-31',
    updated_at      TEXT    NOT NULL,
    mutation_reason TEXT    NOT NULL
);

CREATE TABLE IF NOT EXISTS assignment (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    org_unit_id     INTEGER NOT NULL REFERENCES org_unit(id),
    person_id       INTEGER          REFERENCES person(id),
    role_label      TEXT,
    valid_from      TEXT    NOT NULL,
    valid_until     TEXT    NOT NULL DEFAULT '9999-12-31',
    updated_at      TEXT    NOT NULL,
    mutation_reason TEXT    NOT NULL
);

CREATE TABLE IF NOT EXISTS org_unit_history (
    id              INTEGER NOT NULL,
    name            TEXT    NOT NULL,
    description     TEXT,
    parent_id       INTEGER,
    sort_order      INTEGER NOT NULL DEFAULT 0,
    valid_from      TEXT    NOT NULL,
    valid_until     TEXT    NOT NULL,
    updated_at      TEXT    NOT NULL,
    mutation_reason TEXT    NOT NULL,
    replaced_at     TEXT    NOT NULL
);

CREATE TABLE IF NOT EXISTS person_history (
    id              INTEGER NOT NULL,
    first_name      TEXT    NOT NULL,
    last_name       TEXT    NOT NULL,
    email           TEXT,
    notes           TEXT,
    valid_from      TEXT    NOT NULL,
    valid_until     TEXT    NOT NULL,
    updated_at      TEXT    NOT NULL,
    mutation_reason TEXT    NOT NULL,
    replaced_at     TEXT    NOT NULL
);

CREATE TABLE IF NOT EXISTS assignment_history (
    id              INTEGER NOT NULL,
    org_unit_id     INTEGER NOT NULL,
    person_id       INTEGER,          -- NULL = position was open at this version
    role_label      TEXT,
    valid_from      TEXT    NOT NULL,
    valid_until     TEXT    NOT NULL,
    updated_at      TEXT    NOT NULL,
    mutation_reason TEXT    NOT NULL,
    replaced_at     TEXT    NOT NULL
);
"""

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def utcnow_str() -> str:
    """Return current UTC datetime as ISO string. Monkeypatch in tests."""
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def active_filter(active_only: bool, today: str) -> str:
    """Return a SQL WHERE clause fragment for the active date range.

    Pure function - no DB dependency.
    """
    if not active_only:
        return ""
    return f"WHERE valid_from <= '{today}' AND valid_until >= '{today}'"


async def copy_to_history(
    conn: aiosqlite.Connection,
    table: str,
    row_id: int,
    now: str,
) -> None:
    """Copy the current row from *table* to *table*_history with replaced_at=now."""
    history = f"{table}_history"
    # fetch column names dynamically so this helper works for all 3 tables
    async with conn.execute(f"PRAGMA table_info({table})") as cur:
        cols = [row[1] async for row in cur]
    col_list = ", ".join(cols)
    await conn.execute(
        f"INSERT INTO {history} ({col_list}, replaced_at) "
        f"SELECT {col_list}, ? FROM {table} WHERE id = ?",
        (now, row_id),
    )


# ---------------------------------------------------------------------------
# Init
# ---------------------------------------------------------------------------


async def init_db(db_path: Path = DB_PATH) -> None:
    """Create all tables if they do not exist. Called from app lifespan."""
    db_path.parent.mkdir(parents=True, exist_ok=True)
    async with aiosqlite.connect(str(db_path)) as conn:
        await conn.executescript(_DDL)
        await conn.commit()


# ---------------------------------------------------------------------------
# FastAPI dependency
# ---------------------------------------------------------------------------


async def get_db() -> AsyncGenerator[aiosqlite.Connection, None]:
    """Yield an aiosqlite connection. Override in tests via dependency_overrides."""
    async with aiosqlite.connect(str(DB_PATH)) as conn:
        conn.row_factory = aiosqlite.Row
        await conn.execute("PRAGMA foreign_keys=ON")
        yield conn
