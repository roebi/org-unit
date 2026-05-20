from __future__ import annotations

import pytest_asyncio
import aiosqlite
from httpx import AsyncClient, ASGITransport

from org_unit.database import _DDL, get_db
from org_unit.main import create_app


@pytest_asyncio.fixture
async def db():
    """In-memory SQLite DB with all tables created. Injected into the app."""
    async with aiosqlite.connect(":memory:") as conn:
        conn.row_factory = aiosqlite.Row
        await conn.execute("PRAGMA foreign_keys=ON")
        await conn.executescript(_DDL)
        await conn.commit()
        yield conn


@pytest_asyncio.fixture
async def client(db):
    """AsyncClient wired to a fresh app with the in-memory DB injected."""
    app = create_app()

    async def override_get_db():
        yield db

    app.dependency_overrides[get_db] = override_get_db

    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as ac:
        yield ac


# ---------------------------------------------------------------------------
# Shared factory helpers used across test modules
# ---------------------------------------------------------------------------

async def make_org_unit(client: AsyncClient, **kwargs) -> dict:
    defaults = dict(
        name="Test Unit",
        valid_from="2026-01-01",
        mutation_reason="test setup",
    )
    defaults.update(kwargs)
    r = await client.post("/api/v1/org-units", json=defaults)
    assert r.status_code == 201, r.text
    return r.json()


async def make_person(client: AsyncClient, **kwargs) -> dict:
    defaults = dict(
        first_name="Jane",
        last_name="Doe",
        valid_from="2026-01-01",
        mutation_reason="test setup",
    )
    defaults.update(kwargs)
    r = await client.post("/api/v1/persons", json=defaults)
    assert r.status_code == 201, r.text
    return r.json()


async def make_assignment(client: AsyncClient, org_unit_id: int, person_id: int, **kwargs) -> dict:
    defaults = dict(
        org_unit_id=org_unit_id,
        person_id=person_id,
        valid_from="2026-01-01",
        mutation_reason="test setup",
    )
    defaults.update(kwargs)
    r = await client.post("/api/v1/assignments", json=defaults)
    assert r.status_code == 201, r.text
    return r.json()
