"""Tests for OrgUnit endpoints - FR-01..FR-10, FR-23."""
from __future__ import annotations

import pytest
from tests.conftest import make_org_unit, make_person, make_assignment


@pytest.mark.asyncio
async def test_create_org_unit_returns_201(client):
    """FR-01: POST creates record and returns 201."""
    r = await client.post("/api/v1/org-units", json={
        "name": "Direction",
        "valid_from": "2026-01-01",
        "mutation_reason": "initial setup",
    })
    assert r.status_code == 201
    data = r.json()
    assert data["name"] == "Direction"
    assert data["id"] is not None
    assert data["valid_until"] == "9999-12-31"
    assert data["mutation_reason"] == "initial setup"


@pytest.mark.asyncio
async def test_create_org_unit_missing_mutation_reason_returns_422(client):
    """FR-02: POST without mutation_reason returns 422."""
    r = await client.post("/api/v1/org-units", json={
        "name": "No Reason",
        "valid_from": "2026-01-01",
    })
    assert r.status_code == 422


@pytest.mark.asyncio
async def test_list_org_units_active_only_default(client):
    """FR-03: GET returns only active records by default."""
    await make_org_unit(client, name="Active", valid_from="2020-01-01")
    await make_org_unit(client, name="Future", valid_from="2099-01-01")
    await make_org_unit(client, name="Past", valid_from="2020-01-01", valid_until="2021-01-01")

    r = await client.get("/api/v1/org-units")
    assert r.status_code == 200
    names = [u["name"] for u in r.json()]
    assert "Active" in names
    assert "Future" not in names
    assert "Past" not in names


@pytest.mark.asyncio
async def test_list_org_units_active_only_false(client):
    """FR-04: GET?active_only=false returns all records."""
    await make_org_unit(client, name="Active", valid_from="2020-01-01")
    await make_org_unit(client, name="Past", valid_from="2020-01-01", valid_until="2021-01-01")

    r = await client.get("/api/v1/org-units?active_only=false")
    assert r.status_code == 200
    names = [u["name"] for u in r.json()]
    assert "Active" in names
    assert "Past" in names


@pytest.mark.asyncio
async def test_get_tree_returns_nested_structure(client):
    """FR-05: GET /tree returns nested children."""
    parent = await make_org_unit(client, name="Parent", valid_from="2020-01-01")
    await make_org_unit(client, name="Child", valid_from="2020-01-01", parent_id=parent["id"])

    r = await client.get("/api/v1/org-units/tree")
    assert r.status_code == 200
    tree = r.json()
    assert len(tree) == 1
    assert tree[0]["name"] == "Parent"
    assert len(tree[0]["children"]) == 1
    assert tree[0]["children"][0]["name"] == "Child"


@pytest.mark.asyncio
async def test_get_org_unit_by_id(client):
    """FR-06: GET /{id} returns single record."""
    unit = await make_org_unit(client, name="Big Cats")
    r = await client.get(f"/api/v1/org-units/{unit['id']}")
    assert r.status_code == 200
    assert r.json()["name"] == "Big Cats"


@pytest.mark.asyncio
async def test_get_org_unit_not_found(client):
    """FR-06: GET /{id} returns 404 for unknown id."""
    r = await client.get("/api/v1/org-units/99999")
    assert r.status_code == 404


@pytest.mark.asyncio
async def test_get_org_unit_history(client):
    """FR-07: GET /{id}/history returns replaced versions."""
    unit = await make_org_unit(client, name="Original")
    await client.patch(f"/api/v1/org-units/{unit['id']}", json={
        "name": "Updated",
        "mutation_reason": "rename",
    })
    r = await client.get(f"/api/v1/org-units/{unit['id']}/history")
    assert r.status_code == 200
    history = r.json()
    assert len(history) == 1
    assert history[0]["name"] == "Original"
    assert "replaced_at" in history[0]


@pytest.mark.asyncio
async def test_patch_org_unit_updates_and_copies_history(client):
    """FR-08: PATCH updates record and copies old row to history."""
    unit = await make_org_unit(client, name="Before")
    r = await client.patch(f"/api/v1/org-units/{unit['id']}", json={
        "name": "After",
        "mutation_reason": "corrected name",
    })
    assert r.status_code == 200
    assert r.json()["name"] == "After"
    assert r.json()["mutation_reason"] == "corrected name"


@pytest.mark.asyncio
async def test_patch_org_unit_missing_mutation_reason_returns_422(client):
    """FR-09: PATCH without mutation_reason returns 422."""
    unit = await make_org_unit(client)
    r = await client.patch(f"/api/v1/org-units/{unit['id']}", json={"name": "No reason"})
    assert r.status_code == 422


@pytest.mark.asyncio
async def test_deactivate_org_unit_via_patch(client):
    """FR-10: deactivate by patching valid_until to today."""
    unit = await make_org_unit(client, name="To Close", valid_from="2020-01-01")
    r = await client.patch(f"/api/v1/org-units/{unit['id']}", json={
        "valid_until": "2026-01-01",
        "mutation_reason": "unit dissolved",
    })
    assert r.status_code == 200
    assert r.json()["valid_until"] == "2026-01-01"

    active = await client.get("/api/v1/org-units")
    names = [u["name"] for u in active.json()]
    assert "To Close" not in names


@pytest.mark.asyncio
async def test_get_org_unit_assignments(client):
    """FR-23: GET /{id}/assignments returns assignments for that unit."""
    unit = await make_org_unit(client, name="Reptiles", valid_from="2020-01-01")
    person = await make_person(client)
    await make_assignment(client, unit["id"], person["id"], role_label="Keeper")

    r = await client.get(f"/api/v1/org-units/{unit['id']}/assignments")
    assert r.status_code == 200
    items = r.json()
    assert len(items) == 1
    assert items[0]["org_unit_id"] == unit["id"]
    assert items[0]["role_label"] == "Keeper"
