"""
Duplicate detector service — wrapper for candidate integrity checks.
"""

from typing import Dict
from sqlalchemy.ext.asyncio import AsyncSession
from app.services.candidate_integrity_service import check_duplicate_candidate as _check_duplicate


async def check_duplicate_candidate(
    email: str,
    mobile_number: str,
    db: AsyncSession
) -> Dict:
    """
    Check if candidate is duplicate based on email or phone.
    Wrapper function for backward compatibility.
    """
    return await _check_duplicate(email, mobile_number, db)
