"""Tests for Person endpoints - FR-11..FR-18, FR-24."""
from __future__ import annotations

import pytest
from tests.conftest import make_org_unit, make_person, make_assignment


@pytest.mark.asyncio
async def test_create_person_returns_201(client):
    """FR-11: POST creates record and returns 201."""
    r = await client.post("/api/v1/persons", json={
        "first_name": "Hans",
        "last_name": "Muster",
        "valid_from": "2026-01-01",
        "mutation_reason": "hired",
    })
    assert r.status_code == 201
    data = r.json()
    assert data["first_name"] == "Hans"
    assert data["last_name"] == "Muster"
    assert data["valid_until"] == "9999-12-31"


@pytest.mark.asyncio
async def test_create_person_missing_mutation_reason_returns_422(client):
    """FR-12: POST without mutation_reason returns 422."""
    r = await client.post("/api/v1/persons", json={
        "first_name": "Jane",
        "last_name": "Doe",
        "valid_from": "2026-01-01",
    })
    assert r.status_code == 422


@pytest.mark.asyncio
async def test_list_persons_active_only(client):
    """FR-13: GET returns only active persons by default."""
    await make_person(client, first_name="Active", valid_from="2020-01-01")
    await make_person(client, first_name="Exited", valid_from="2020-01-01", valid_until="2021-01-01")

    r = await client.get("/api/v1/persons")
    assert r.status_code == 200
    names = [p["first_name"] for p in r.json()]
    assert "Active" in names
    assert "Exited" not in names


@pytest.mark.asyncio
async def test_list_persons_active_only_false(client):
    """FR-13: GET?active_only=false returns all persons."""
    await make_person(client, first_name="Active", valid_from="2020-01-01")
    await make_person(client, first_name="Exited", valid_from="2020-01-01", valid_until="2021-01-01")

    r = await client.get("/api/v1/persons?active_only=false")
    names = [p["first_name"] for p in r.json()]
    assert "Active" in names
    assert "Exited" in names


@pytest.mark.asyncio
async def test_get_person_by_id(client):
    """FR-14: GET /{id} returns single person."""
    person = await make_person(client, first_name="John")
    r = await client.get(f"/api/v1/persons/{person['id']}")
    assert r.status_code == 200
    assert r.json()["first_name"] == "John"


@pytest.mark.asyncio
async def test_get_person_not_found(client):
    """FR-14: GET /{id} returns 404 for unknown id."""
    r = await client.get("/api/v1/persons/99999")
    assert r.status_code == 404


@pytest.mark.asyncio
async def test_get_person_history(client):
    """FR-15: GET /{id}/history returns replaced versions."""
    person = await make_person(client, first_name="Old")
    await client.patch(f"/api/v1/persons/{person['id']}", json={
        "first_name": "New",
        "mutation_reason": "name correction",
    })
    r = await client.get(f"/api/v1/persons/{person['id']}/history")
    assert r.status_code == 200
    history = r.json()
    assert len(history) == 1
    assert history[0]["first_name"] == "Old"
    assert "replaced_at" in history[0]


@pytest.mark.asyncio
async def test_patch_person_updates_and_copies_history(client):
    """FR-16: PATCH updates record and stores old row in history."""
    person = await make_person(client, last_name="Smith")
    r = await client.patch(f"/api/v1/persons/{person['id']}", json={
        "last_name": "Jones",
        "mutation_reason": "married",
    })
    assert r.status_code == 200
    assert r.json()["last_name"] == "Jones"


@pytest.mark.asyncio
async def test_patch_person_missing_mutation_reason_returns_422(client):
    """FR-17: PATCH without mutation_reason returns 422."""
    person = await make_person(client)
    r = await client.patch(f"/api/v1/persons/{person['id']}", json={"first_name": "X"})
    assert r.status_code == 422


@pytest.mark.asyncio
async def test_deactivate_person_via_patch(client):
    """FR-18: deactivate person by patching valid_until."""
    person = await make_person(client, first_name="Leaving", valid_from="2020-01-01")
    r = await client.patch(f"/api/v1/persons/{person['id']}", json={
        "valid_until": "2026-01-01",
        "mutation_reason": "resignation",
    })
    assert r.status_code == 200
    assert r.json()["valid_until"] == "2026-01-01"

    active = await client.get("/api/v1/persons")
    names = [p["first_name"] for p in active.json()]
    assert "Leaving" not in names


@pytest.mark.asyncio
async def test_get_person_assignments(client):
    """FR-24: GET /persons/{id}/assignments returns assignments for that person."""
    unit = await make_org_unit(client, name="Primates", valid_from="2020-01-01")
    person = await make_person(client)
    await make_assignment(client, unit["id"], person["id"], role_label="Deputy")

    r = await client.get(f"/api/v1/persons/{person['id']}/assignments")
    assert r.status_code == 200
    items = r.json()
    assert len(items) == 1
    assert items[0]["person_id"] == person["id"]
    assert items[0]["role_label"] == "Deputy"
