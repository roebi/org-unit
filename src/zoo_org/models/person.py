from __future__ import annotations

from typing import Optional

from pydantic import BaseModel, Field


class PersonCreate(BaseModel):
    first_name: str
    last_name: str
    email: Optional[str] = None
    notes: Optional[str] = None
    valid_from: str
    valid_until: str = "9999-12-31"
    mutation_reason: str = Field(..., min_length=1)


class PersonPatch(BaseModel):
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    email: Optional[str] = None
    notes: Optional[str] = None
    valid_from: Optional[str] = None
    valid_until: Optional[str] = None
    mutation_reason: str = Field(..., min_length=1)


class PersonOut(BaseModel):
    id: int
    first_name: str
    last_name: str
    email: Optional[str]
    notes: Optional[str]
    valid_from: str
    valid_until: str
    updated_at: str
    mutation_reason: str


class PersonHistoryOut(PersonOut):
    replaced_at: str
