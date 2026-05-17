from __future__ import annotations

from typing import Optional

from pydantic import BaseModel, Field


class OrgUnitCreate(BaseModel):
    name: str
    description: Optional[str] = None
    parent_id: Optional[int] = None
    sort_order: int = 0
    valid_from: str
    valid_until: str = "9999-12-31"
    mutation_reason: str = Field(..., min_length=1)


class OrgUnitPatch(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    parent_id: Optional[int] = None
    sort_order: Optional[int] = None
    valid_from: Optional[str] = None
    valid_until: Optional[str] = None
    mutation_reason: str = Field(..., min_length=1)


class OrgUnitOut(BaseModel):
    id: int
    name: str
    description: Optional[str]
    parent_id: Optional[int]
    sort_order: int
    valid_from: str
    valid_until: str
    updated_at: str
    mutation_reason: str


class OrgUnitHistoryOut(OrgUnitOut):
    replaced_at: str


class OrgUnitNode(OrgUnitOut):
    children: list[OrgUnitNode] = []
