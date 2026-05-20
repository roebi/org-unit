"""Tests for FR-29..FR-32 and pure helper functions."""
from __future__ import annotations

import pytest
from org_unit.database import active_filter
from org_unit.routers.org_units import build_tree


# ---------------------------------------------------------------------------
# FR-29 / FR-30: tables exist and NOT NULL enforced
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_all_tables_created(db):
    """FR-29: init creates all 6 tables."""
    async with db.execute(
        "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name"
    ) as cur:
        tables = {row[0] async for row in cur}
    expected = {
        "org_unit", "person", "assignment",
        "org_unit_history", "person_history", "assignment_history",
    }
    assert expected.issubset(tables)


@pytest.mark.asyncio
async def test_valid_from_not_null_enforced(db):
    """FR-30: valid_from NOT NULL raises on insert."""
    import aiosqlite
    with pytest.raises(aiosqlite.IntegrityError):
        await db.execute(
            "INSERT INTO org_unit (name, valid_from, valid_until, updated_at, mutation_reason)"
            " VALUES ('X', NULL, '9999-12-31', '2026-01-01', 'test')"
        )


# ---------------------------------------------------------------------------
# FR-31: sentinel default
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_sentinel_default_via_api(client):
    """FR-31: omitting valid_until defaults to 9999-12-31."""
    r = await client.post("/api/v1/org-units", json={
        "name": "Sentinel Test",
        "valid_from": "2026-01-01",
        "mutation_reason": "sentinel check",
    })
    assert r.status_code == 201
    assert r.json()["valid_until"] == "9999-12-31"


# ---------------------------------------------------------------------------
# FR-32: copy_to_history on PATCH
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_patch_copies_row_to_history(client, db):
    """FR-32: PATCH moves current row to history before writing new state."""
    r = await client.post("/api/v1/org-units", json={
        "name": "Before",
        "valid_from": "2026-01-01",
        "mutation_reason": "initial",
    })
    uid = r.json()["id"]

    await client.patch(f"/api/v1/org-units/{uid}", json={
        "name": "After",
        "mutation_reason": "rename",
    })

    async with db.execute(
        "SELECT name, mutation_reason FROM org_unit_history WHERE id = ?", (uid,)
    ) as cur:
        history = await cur.fetchall()

    assert len(history) == 1
    assert history[0]["name"] == "Before"
    assert history[0]["mutation_reason"] == "initial"


# ---------------------------------------------------------------------------
# Pure function: active_filter
# ---------------------------------------------------------------------------

def test_active_filter_returns_where_clause():
    clause = active_filter(True, "2026-05-16")
    assert "valid_from" in clause
    assert "valid_until" in clause
    assert "2026-05-16" in clause


def test_active_filter_inactive_returns_empty():
    assert active_filter(False, "2026-05-16") == ""


# ---------------------------------------------------------------------------
# Pure function: build_tree
# ---------------------------------------------------------------------------

def test_build_tree_flat_list():
    rows = [
        {"id": 1, "parent_id": None, "name": "Root", "sort_order": 0},
        {"id": 2, "parent_id": 1,    "name": "Child", "sort_order": 0},
    ]
    tree = build_tree(rows)
    assert len(tree) == 1
    assert tree[0]["name"] == "Root"
    assert tree[0]["children"][0]["name"] == "Child"


def test_build_tree_multiple_roots():
    rows = [
        {"id": 1, "parent_id": None, "name": "A", "sort_order": 0},
        {"id": 2, "parent_id": None, "name": "B", "sort_order": 1},
    ]
    tree = build_tree(rows)
    assert len(tree) == 2


def test_build_tree_empty():
    assert build_tree([]) == []
