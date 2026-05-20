from __future__ import annotations

from datetime import date
from typing import Annotated

import aiosqlite
from fastapi import APIRouter, Depends, HTTPException

from org_unit.database import active_filter, copy_to_history, get_db, utcnow_str
from org_unit.models.assignment import (
    AssignmentCreate,
    AssignmentHistoryOut,
    AssignmentOut,
    AssignmentPatch,
)

router = APIRouter(prefix="/assignments", tags=["assignments"])

DbDep = Annotated[aiosqlite.Connection, Depends(get_db)]


def _row_to_dict(row: aiosqlite.Row) -> dict:
    return dict(row)


@router.get("", response_model=list[AssignmentOut])
async def list_assignments(db: DbDep, active_only: bool = True):
    today = date.today().isoformat()
    where = active_filter(active_only, today)
    async with db.execute(f"SELECT * FROM assignment {where} ORDER BY id") as cur:
        rows = await cur.fetchall()
    return [_row_to_dict(r) for r in rows]


@router.get("/{assignment_id}/history", response_model=list[AssignmentHistoryOut])
async def get_assignment_history(assignment_id: int, db: DbDep):
    async with db.execute(
        "SELECT * FROM assignment_history WHERE id = ? ORDER BY replaced_at DESC",
        (assignment_id,),
    ) as cur:
        rows = await cur.fetchall()
    return [_row_to_dict(r) for r in rows]


@router.get("/{assignment_id}", response_model=AssignmentOut)
async def get_assignment(assignment_id: int, db: DbDep):
    async with db.execute(
        "SELECT * FROM assignment WHERE id = ?", (assignment_id,)
    ) as cur:
        row = await cur.fetchone()
    if row is None:
        raise HTTPException(status_code=404, detail="Assignment not found")
    return _row_to_dict(row)


@router.post("", response_model=AssignmentOut, status_code=201)
async def create_assignment(payload: AssignmentCreate, db: DbDep):
    # FR-21: explicit FK check -> meaningful 422, not a 500
    async with db.execute(
        "SELECT id FROM org_unit WHERE id = ?", (payload.org_unit_id,)
    ) as cur:
        if await cur.fetchone() is None:
            raise HTTPException(
                status_code=422, detail=f"org_unit_id {payload.org_unit_id} not found"
            )
    # FR-19b: person_id is optional (NULL = open position); only check when provided
    if payload.person_id is not None:
        async with db.execute(
            "SELECT id FROM person WHERE id = ?", (payload.person_id,)
        ) as cur:
            if await cur.fetchone() is None:
                raise HTTPException(
                    status_code=422, detail=f"person_id {payload.person_id} not found"
                )

    now = utcnow_str()
    async with db.execute(
        """INSERT INTO assignment
           (org_unit_id, person_id, role_label,
            valid_from, valid_until, updated_at, mutation_reason)
           VALUES (?, ?, ?, ?, ?, ?, ?)""",
        (
            payload.org_unit_id,
            payload.person_id,
            payload.role_label,
            payload.valid_from,
            payload.valid_until,
            now,
            payload.mutation_reason,
        ),
    ) as cur:
        new_id = cur.lastrowid
    await db.commit()
    async with db.execute("SELECT * FROM assignment WHERE id = ?", (new_id,)) as cur:
        row = await cur.fetchone()
    return _row_to_dict(row)


@router.patch("/{assignment_id}", response_model=AssignmentOut)
async def update_assignment(assignment_id: int, payload: AssignmentPatch, db: DbDep):
    async with db.execute(
        "SELECT * FROM assignment WHERE id = ?", (assignment_id,)
    ) as cur:
        existing = await cur.fetchone()
    if existing is None:
        raise HTTPException(status_code=404, detail="Assignment not found")

    now = utcnow_str()
    await copy_to_history(db, "assignment", assignment_id, now)

    current = _row_to_dict(existing)
    for key, val in payload.model_dump(exclude_unset=True).items():
        if key != "mutation_reason":
            current[key] = val
    current["mutation_reason"] = payload.mutation_reason
    current["updated_at"] = now

    await db.execute(
        """UPDATE assignment SET
           org_unit_id=?, person_id=?, role_label=?,
           valid_from=?, valid_until=?, updated_at=?, mutation_reason=?
           WHERE id=?""",
        (
            current["org_unit_id"],
            current["person_id"],
            current["role_label"],
            current["valid_from"],
            current["valid_until"],
            current["updated_at"],
            current["mutation_reason"],
            assignment_id,
        ),
    )
    await db.commit()
    async with db.execute(
        "SELECT * FROM assignment WHERE id = ?", (assignment_id,)
    ) as cur:
        row = await cur.fetchone()
    return _row_to_dict(row)
