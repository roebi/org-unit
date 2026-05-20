from __future__ import annotations

from datetime import date
from typing import Annotated

import aiosqlite
from fastapi import APIRouter, Depends, HTTPException

from org_unit.database import active_filter, copy_to_history, get_db, utcnow_str
from org_unit.models.assignment import AssignmentOut
from org_unit.models.org_unit import (
    OrgUnitCreate,
    OrgUnitHistoryOut,
    OrgUnitNode,
    OrgUnitOut,
    OrgUnitPatch,
)

router = APIRouter(prefix="/org-units", tags=["org-units"])

DbDep = Annotated[aiosqlite.Connection, Depends(get_db)]


def _row_to_dict(row: aiosqlite.Row) -> dict:
    return dict(row)


def build_tree(rows: list[dict]) -> list[dict]:
    """Assemble flat org_unit rows into a nested tree. Pure function."""
    by_id: dict[int, dict] = {}
    for row in rows:
        node = dict(row)
        node["children"] = []
        by_id[node["id"]] = node
    roots = []
    for node in by_id.values():
        pid = node.get("parent_id")
        if pid and pid in by_id:
            by_id[pid]["children"].append(node)
        else:
            roots.append(node)
    return roots


@router.get("", response_model=list[OrgUnitOut])
async def list_org_units(db: DbDep, active_only: bool = True):
    today = date.today().isoformat()
    where = active_filter(active_only, today)
    async with db.execute(f"SELECT * FROM org_unit {where} ORDER BY sort_order") as cur:
        rows = await cur.fetchall()
    return [_row_to_dict(r) for r in rows]


@router.get("/tree", response_model=list[OrgUnitNode])
async def get_tree(db: DbDep):
    today = date.today().isoformat()
    where = active_filter(True, today)
    async with db.execute(f"SELECT * FROM org_unit {where} ORDER BY sort_order") as cur:
        rows = await cur.fetchall()
    return build_tree([_row_to_dict(r) for r in rows])


@router.get("/{org_unit_id}/history", response_model=list[OrgUnitHistoryOut])
async def get_org_unit_history(org_unit_id: int, db: DbDep):
    async with db.execute(
        "SELECT * FROM org_unit_history WHERE id = ? ORDER BY replaced_at DESC",
        (org_unit_id,),
    ) as cur:
        rows = await cur.fetchall()
    return [_row_to_dict(r) for r in rows]


@router.get("/{org_unit_id}/assignments", response_model=list[AssignmentOut])
async def get_org_unit_assignments(org_unit_id: int, db: DbDep, active_only: bool = True):
    today = date.today().isoformat()
    extra = (
        f"AND valid_from <= '{today}' AND valid_until >= '{today}'"
        if active_only
        else ""
    )
    async with db.execute(
        f"SELECT * FROM assignment WHERE org_unit_id = ? {extra}",
        (org_unit_id,),
    ) as cur:
        rows = await cur.fetchall()
    return [_row_to_dict(r) for r in rows]


@router.get("/{org_unit_id}", response_model=OrgUnitOut)
async def get_org_unit(org_unit_id: int, db: DbDep):
    async with db.execute(
        "SELECT * FROM org_unit WHERE id = ?", (org_unit_id,)
    ) as cur:
        row = await cur.fetchone()
    if row is None:
        raise HTTPException(status_code=404, detail="OrgUnit not found")
    return _row_to_dict(row)


@router.post("", response_model=OrgUnitOut, status_code=201)
async def create_org_unit(payload: OrgUnitCreate, db: DbDep):
    now = utcnow_str()
    async with db.execute(
        """INSERT INTO org_unit
           (name, description, parent_id, sort_order,
            valid_from, valid_until, updated_at, mutation_reason)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
        (
            payload.name,
            payload.description,
            payload.parent_id,
            payload.sort_order,
            payload.valid_from,
            payload.valid_until,
            now,
            payload.mutation_reason,
        ),
    ) as cur:
        new_id = cur.lastrowid
    await db.commit()
    async with db.execute("SELECT * FROM org_unit WHERE id = ?", (new_id,)) as cur:
        row = await cur.fetchone()
    return _row_to_dict(row)


@router.patch("/{org_unit_id}", response_model=OrgUnitOut)
async def update_org_unit(org_unit_id: int, payload: OrgUnitPatch, db: DbDep):
    async with db.execute(
        "SELECT * FROM org_unit WHERE id = ?", (org_unit_id,)
    ) as cur:
        existing = await cur.fetchone()
    if existing is None:
        raise HTTPException(status_code=404, detail="OrgUnit not found")

    now = utcnow_str()
    await copy_to_history(db, "org_unit", org_unit_id, now)

    current = _row_to_dict(existing)
    updates = payload.model_dump(exclude_unset=True)
    for key, val in updates.items():
        if key != "mutation_reason":
            current[key] = val
    current["mutation_reason"] = payload.mutation_reason
    current["updated_at"] = now

    await db.execute(
        """UPDATE org_unit SET
           name=?, description=?, parent_id=?, sort_order=?,
           valid_from=?, valid_until=?, updated_at=?, mutation_reason=?
           WHERE id=?""",
        (
            current["name"],
            current["description"],
            current["parent_id"],
            current["sort_order"],
            current["valid_from"],
            current["valid_until"],
            current["updated_at"],
            current["mutation_reason"],
            org_unit_id,
        ),
    )
    await db.commit()
    async with db.execute("SELECT * FROM org_unit WHERE id = ?", (org_unit_id,)) as cur:
        row = await cur.fetchone()
    return _row_to_dict(row)
