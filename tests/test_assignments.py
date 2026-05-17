"""Tests for Assignment endpoints - FR-19..FR-28."""
from __future__ import annotations

import pytest
from tests.conftest import make_org_unit, make_person, make_assignment


@pytest.mark.asyncio
async def test_create_assignment_returns_201(client):
    """FR-19: POST creates assignment and returns 201."""
    unit = await make_org_unit(client, valid_from="2020-01-01")
    person = await make_person(client)
    r = await client.post("/api/v1/assignments", json={
        "org_unit_id": unit["id"],
        "person_id": person["id"],
        "role_label": "Head",
        "valid_from": "2026-01-01",
        "mutation_reason": "appointed",
    })
    assert r.status_code == 201
    data = r.json()
    assert data["role_label"] == "Head"
    assert data["org_unit_id"] == unit["id"]
    assert data["person_id"] == person["id"]


@pytest.mark.asyncio
async def test_create_assignment_missing_mutation_reason_returns_422(client):
    """FR-20: POST without mutation_reason returns 422."""
    unit = await make_org_unit(client, valid_from="2020-01-01")
    person = await make_person(client)
    r = await client.post("/api/v1/assignments", json={
        "org_unit_id": unit["id"],
        "person_id": person["id"],
        "valid_from": "2026-01-01",
    })
    assert r.status_code == 422


@pytest.mark.asyncio
async def test_create_assignment_bad_org_unit_fk_returns_422(client):
    """FR-21: POST with non-existent org_unit_id returns 422."""
    person = await make_person(client)
    r = await client.post("/api/v1/assignments", json={
        "org_unit_id": 99999,
        "person_id": person["id"],
        "valid_from": "2026-01-01",
        "mutation_reason": "bad fk test",
    })
    assert r.status_code == 422


@pytest.mark.asyncio
async def test_create_assignment_bad_person_fk_returns_422(client):
    """FR-21: POST with non-existent person_id returns 422."""
    unit = await make_org_unit(client, valid_from="2020-01-01")
    r = await client.post("/api/v1/assignments", json={
        "org_unit_id": unit["id"],
        "person_id": 99999,
        "valid_from": "2026-01-01",
        "mutation_reason": "bad fk test",
    })
    assert r.status_code == 422


@pytest.mark.asyncio
async def test_list_assignments_active_only(client):
    """FR-22: GET returns only active assignments by default."""
    unit = await make_org_unit(client, valid_from="2020-01-01")
    p1 = await make_person(client, first_name="Active")
    p2 = await make_person(client, first_name="Past")
    await make_assignment(client, unit["id"], p1["id"])
    past = await make_assignment(client, unit["id"], p2["id"])
    await client.patch(f"/api/v1/assignments/{past['id']}", json={
        "valid_until": "2021-01-01",
        "mutation_reason": "ended",
    })

    r = await client.get("/api/v1/assignments")
    assert r.status_code == 200
    ids = [a["person_id"] for a in r.json()]
    assert p1["id"] in ids
    assert p2["id"] not in ids


@pytest.mark.asyncio
async def test_list_assignments_active_only_false(client):
    """FR-22: GET?active_only=false returns all assignments."""
    unit = await make_org_unit(client, valid_from="2020-01-01")
    person = await make_person(client)
    a = await make_assignment(client, unit["id"], person["id"])
    await client.patch(f"/api/v1/assignments/{a['id']}", json={
        "valid_until": "2021-01-01",
        "mutation_reason": "ended",
    })

    r = await client.get("/api/v1/assignments?active_only=false")
    assert r.status_code == 200
    assert len(r.json()) >= 1


@pytest.mark.asyncio
async def test_get_assignment_history(client):
    """FR-25: GET /{id}/history returns replaced versions."""
    unit = await make_org_unit(client, valid_from="2020-01-01")
    person = await make_person(client)
    a = await make_assignment(client, unit["id"], person["id"], role_label="Intern")

    await client.patch(f"/api/v1/assignments/{a['id']}", json={
        "role_label": "Head",
        "mutation_reason": "promoted",
    })

    r = await client.get(f"/api/v1/assignments/{a['id']}/history")
    assert r.status_code == 200
    history = r.json()
    assert len(history) == 1
    assert history[0]["role_label"] == "Intern"
    assert "replaced_at" in history[0]


@pytest.mark.asyncio
async def test_patch_assignment_updates_and_copies_history(client):
    """FR-26: PATCH updates assignment and copies old row to history."""
    unit = await make_org_unit(client, valid_from="2020-01-01")
    person = await make_person(client)
    a = await make_assignment(client, unit["id"], person["id"], role_label="Intern")

    r = await client.patch(f"/api/v1/assignments/{a['id']}", json={
        "role_label": "Deputy",
        "mutation_reason": "role changed",
    })
    assert r.status_code == 200
    assert r.json()["role_label"] == "Deputy"
    assert r.json()["mutation_reason"] == "role changed"


@pytest.mark.asyncio
async def test_patch_assignment_missing_mutation_reason_returns_422(client):
    """FR-27: PATCH without mutation_reason returns 422."""
    unit = await make_org_unit(client, valid_from="2020-01-01")
    person = await make_person(client)
    a = await make_assignment(client, unit["id"], person["id"])
    r = await client.patch(f"/api/v1/assignments/{a['id']}", json={"role_label": "X"})
    assert r.status_code == 422


@pytest.mark.asyncio
async def test_deactivate_assignment_via_patch(client):
    """FR-28: deactivate assignment by patching valid_until."""
    unit = await make_org_unit(client, valid_from="2020-01-01")
    person = await make_person(client)
    a = await make_assignment(client, unit["id"], person["id"])

    r = await client.patch(f"/api/v1/assignments/{a['id']}", json={
        "valid_until": "2026-01-01",
        "mutation_reason": "assignment ended",
    })
    assert r.status_code == 200
    assert r.json()["valid_until"] == "2026-01-01"

    active = await client.get("/api/v1/assignments")
    ids = [x["id"] for x in active.json()]
    assert a["id"] not in ids


@pytest.mark.asyncio
async def test_create_assignment_without_person_returns_201(client):
    """FR-19b: POST without person_id creates an open (unfilled) position."""
    unit = await make_org_unit(client, valid_from="2020-01-01")
    r = await client.post("/api/v1/assignments", json={
        "org_unit_id": unit["id"],
        "role_label": "Head",
        "valid_from": "2026-01-01",
        "mutation_reason": "position defined, not yet filled",
    })
    assert r.status_code == 201
    data = r.json()
    assert data["person_id"] is None
    assert data["role_label"] == "Head"
    assert data["org_unit_id"] == unit["id"]


@pytest.mark.asyncio
async def test_fill_open_position_via_patch(client):
    """FR-19c: PATCH person_id to fill an open position."""
    unit = await make_org_unit(client, valid_from="2020-01-01")
    person = await make_person(client)
    # create open position
    r = await client.post("/api/v1/assignments", json={
        "org_unit_id": unit["id"],
        "role_label": "Head",
        "valid_from": "2026-01-01",
        "mutation_reason": "position defined",
    })
    assert r.status_code == 201
    a_id = r.json()["id"]

    # fill it
    r2 = await client.patch(f"/api/v1/assignments/{a_id}", json={
        "person_id": person["id"],
        "mutation_reason": "position filled",
    })
    assert r2.status_code == 200
    assert r2.json()["person_id"] == person["id"]


@pytest.mark.asyncio
async def test_vacate_filled_position_via_patch(client):
    """FR-19c: PATCH person_id to null to vacate a filled position."""
    unit = await make_org_unit(client, valid_from="2020-01-01")
    person = await make_person(client)
    a = await make_assignment(client, unit["id"], person["id"])

    r = await client.patch(f"/api/v1/assignments/{a['id']}", json={
        "person_id": None,
        "mutation_reason": "person left, position now open",
    })
    assert r.status_code == 200
    assert r.json()["person_id"] is None
