from __future__ import annotations

from datetime import date
from typing import Annotated

import aiosqlite
from fastapi import APIRouter, Depends, HTTPException

from src.database import active_filter, copy_to_history, get_db, utcnow_str
from src.models.assignment import AssignmentOut
from src.models.person import PersonCreate, PersonHistoryOut, PersonOut, PersonPatch

router = APIRouter(prefix="/persons", tags=["persons"])

DbDep = Annotated[aiosqlite.Connection, Depends(get_db)]


def _row_to_dict(row: aiosqlite.Row) -> dict:
    return dict(row)


@router.get("", response_model=list[PersonOut])
async def list_persons(db: DbDep, active_only: bool = True):
    today = date.today().isoformat()
    where = active_filter(active_only, today)
    async with db.execute(f"SELECT * FROM person {where} ORDER BY last_name, first_name") as cur:
        rows = await cur.fetchall()
    return [_row_to_dict(r) for r in rows]


@router.get("/{person_id}/history", response_model=list[PersonHistoryOut])
async def get_person_history(person_id: int, db: DbDep):
    async with db.execute(
        "SELECT * FROM person_history WHERE id = ? ORDER BY replaced_at DESC",
        (person_id,),
    ) as cur:
        rows = await cur.fetchall()
    return [_row_to_dict(r) for r in rows]


@router.get("/{person_id}/assignments", response_model=list[AssignmentOut])
async def get_person_assignments(person_id: int, db: DbDep, active_only: bool = True):
    today = date.today().isoformat()
    extra = (
        f"AND valid_from <= '{today}' AND valid_until >= '{today}'"
        if active_only
        else ""
    )
    async with db.execute(
        f"SELECT * FROM assignment WHERE person_id = ? {extra}",
        (person_id,),
    ) as cur:
        rows = await cur.fetchall()
    return [_row_to_dict(r) for r in rows]


@router.get("/{person_id}", response_model=PersonOut)
async def get_person(person_id: int, db: DbDep):
    async with db.execute("SELECT * FROM person WHERE id = ?", (person_id,)) as cur:
        row = await cur.fetchone()
    if row is None:
        raise HTTPException(status_code=404, detail="Person not found")
    return _row_to_dict(row)


@router.post("", response_model=PersonOut, status_code=201)
async def create_person(payload: PersonCreate, db: DbDep):
    now = utcnow_str()
    async with db.execute(
        """INSERT INTO person
           (first_name, last_name, email, notes,
            valid_from, valid_until, updated_at, mutation_reason)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
        (
            payload.first_name,
            payload.last_name,
            payload.email,
            payload.notes,
            payload.valid_from,
            payload.valid_until,
            now,
            payload.mutation_reason,
        ),
    ) as cur:
        new_id = cur.lastrowid
    await db.commit()
    async with db.execute("SELECT * FROM person WHERE id = ?", (new_id,)) as cur:
        row = await cur.fetchone()
    return _row_to_dict(row)


@router.patch("/{person_id}", response_model=PersonOut)
async def update_person(person_id: int, payload: PersonPatch, db: DbDep):
    async with db.execute("SELECT * FROM person WHERE id = ?", (person_id,)) as cur:
        existing = await cur.fetchone()
    if existing is None:
        raise HTTPException(status_code=404, detail="Person not found")

    now = utcnow_str()
    await copy_to_history(db, "person", person_id, now)

    current = _row_to_dict(existing)
    for key, val in payload.model_dump(exclude_unset=True).items():
        if key != "mutation_reason":
            current[key] = val
    current["mutation_reason"] = payload.mutation_reason
    current["updated_at"] = now

    await db.execute(
        """UPDATE person SET
           first_name=?, last_name=?, email=?, notes=?,
           valid_from=?, valid_until=?, updated_at=?, mutation_reason=?
           WHERE id=?""",
        (
            current["first_name"],
            current["last_name"],
            current["email"],
            current["notes"],
            current["valid_from"],
            current["valid_until"],
            current["updated_at"],
            current["mutation_reason"],
            person_id,
        ),
    )
    await db.commit()
    async with db.execute("SELECT * FROM person WHERE id = ?", (person_id,)) as cur:
        row = await cur.fetchone()
    return _row_to_dict(row)
