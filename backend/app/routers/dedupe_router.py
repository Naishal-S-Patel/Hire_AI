"""
Deduplication router — scan for duplicates and merge candidates.
"""

from __future__ import annotations

import uuid
from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import get_db
from app.models.candidate import Candidate

router = APIRouter(prefix="/api/v1/dedupe", tags=["deduplication"])


class DedupeScanRequest(BaseModel):
    threshold: float = 0.85


class DedupeScanResult(BaseModel):
    duplicates: list[dict[str, Any]] = Field(default_factory=list)
    total_pairs: int = 0


class MergeRequest(BaseModel):
    primary_id: uuid.UUID
    duplicate_ids: list[uuid.UUID]


class MergeResult(BaseModel):
    primary_id: uuid.UUID
    merged_count: int
    message: str


@router.post("/scan", response_model=DedupeScanResult, summary="Scan for duplicate candidates")
async def dedupe_scan(body: DedupeScanRequest):
    """
    Scan all candidate embeddings for duplicates above the similarity threshold.
    """
    from app.ml.dedupe.dedupe_engine import scan_all_duplicates

    duplicates = scan_all_duplicates(threshold=body.threshold)
    return DedupeScanResult(
        duplicates=duplicates,
        total_pairs=len(duplicates),
    )


@router.post("/merge", response_model=MergeResult, summary="Merge duplicate candidates")
async def dedupe_merge(body: MergeRequest, db: AsyncSession = Depends(get_db)):
    """
    Merge duplicate candidates into a single canonical record.

    The primary candidate is kept; duplicates get their canonical_id
    pointed to the primary.
    """
    # Verify primary exists
    primary_result = await db.execute(select(Candidate).where(Candidate.id == body.primary_id))
    primary = primary_result.scalar_one_or_none()
    if not primary:
        raise HTTPException(status_code=404, detail="Primary candidate not found")

    merged_count = 0
    for dup_id in body.duplicate_ids:
        dup_result = await db.execute(select(Candidate).where(Candidate.id == dup_id))
        dup = dup_result.scalar_one_or_none()
        if dup and dup.id != primary.id:
            dup.canonical_id = primary.id

            # Merge skills
            primary_skills = set(primary.skills or [])
            dup_skills = set(dup.skills or [])
            primary.skills = sorted(primary_skills | dup_skills)

            merged_count += 1

    await db.flush()

    return MergeResult(
        primary_id=body.primary_id,
        merged_count=merged_count,
        message=f"Merged {merged_count} duplicate(s) into primary candidate.",
    )
