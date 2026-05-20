from __future__ import annotations

from typing import Optional

from pydantic import BaseModel, Field


class AssignmentCreate(BaseModel):
    org_unit_id: int
    person_id: Optional[int] = None
    role_label: Optional[str] = None
    valid_from: str
    valid_until: str = "9999-12-31"
    mutation_reason: str = Field(..., min_length=1)


class AssignmentPatch(BaseModel):
    org_unit_id: Optional[int] = None
    person_id: Optional[int] = None
    role_label: Optional[str] = None
    valid_from: Optional[str] = None
    valid_until: Optional[str] = None
    mutation_reason: str = Field(..., min_length=1)


class AssignmentOut(BaseModel):
    id: int
    org_unit_id: int
    person_id: Optional[int] = None
    role_label: Optional[str]
    valid_from: str
    valid_until: str
    updated_at: str
    mutation_reason: str


class AssignmentHistoryOut(AssignmentOut):
    replaced_at: str
