"""
Candidate Integrity System — AI-powered fraud detection and duplicate prevention.
"""

import hashlib
from typing import Dict, List, Optional
from sqlalchemy import select, or_
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.candidate import Candidate


async def check_duplicate_email(email: str, db: AsyncSession) -> Optional[Candidate]:
    """Check if candidate with same email exists."""
    result = await db.execute(
        select(Candidate).where(Candidate.email == email)
    )
    return result.scalar_one_or_none()


async def check_duplicate_phone(phone: str, db: AsyncSession) -> Optional[Candidate]:
    """Check if candidate with same phone exists."""
    result = await db.execute(
        select(Candidate).where(
            or_(
                Candidate.phone == phone,
                Candidate.mobile_number == phone
            )
        )
    )
    return result.scalar_one_or_none()


async def check_duplicate_resume_hash(resume_hash: str, db: AsyncSession) -> Optional[Candidate]:
    """Check if candidate with same resume hash exists."""
    result = await db.execute(
        select(Candidate).where(Candidate.resume_hash == resume_hash)
    )
    return result.scalar_one_or_none()


async def calculate_resume_similarity(candidate: Candidate, db: AsyncSession) -> List[Dict]:
    """
    Calculate resume text similarity with existing candidates.
    Returns list of similar candidates with similarity scores.
    """
    if not candidate.resume_text:
        return []
    
    # Fetch all other candidates with resume text
    result = await db.execute(
        select(Candidate).where(
            Candidate.id != candidate.id,
            Candidate.resume_text != None,
            Candidate.resume_text != ""
        )
    )
    other_candidates = result.scalars().all()
    
    similar_candidates = []
    candidate_text_lower = candidate.resume_text.lower()
    candidate_words = set(candidate_text_lower.split())
    
    for other in other_candidates:
        if not other.resume_text:
            continue
        
        other_text_lower = other.resume_text.lower()
        other_words = set(other_text_lower.split())
        
        # Calculate Jaccard similarity
        if not candidate_words or not other_words:
            continue
        
        intersection = len(candidate_words & other_words)
        union = len(candidate_words | other_words)
        
        if union == 0:
            continue
        
        similarity = intersection / union
        
        # Flag if similarity > 70%
        if similarity > 0.7:
            similar_candidates.append({
                "candidate_id": str(other.id),
                "candidate_name": other.full_name,
                "similarity_score": round(similarity * 100, 2),
                "match_type": "resume_text"
            })
    
    return similar_candidates


async def calculate_fraud_score(candidate: Candidate, db: AsyncSession) -> Dict:
    """
    Calculate comprehensive fraud score for candidate.
    
    Returns:
        {
            "fraud_score": float (0-100),
            "is_flagged": bool,
            "is_duplicate": bool,
            "fraud_reason": str,
            "flags": List[Dict]
        }
    """
    flags = []
    fraud_score = 0
    is_duplicate = False
    fraud_reasons = []
    
    # 1. Check duplicate email
    if candidate.email and "placeholder" not in candidate.email:
        dup_email = await check_duplicate_email(candidate.email, db)
        if dup_email and dup_email.id != candidate.id:
            flags.append({
                "type": "duplicate_email",
                "severity": "high",
                "message": f"Email already exists for candidate: {dup_email.full_name}",
                "existing_candidate_id": str(dup_email.id)
            })
            fraud_score += 40
            is_duplicate = True
            fraud_reasons.append("Duplicate email")
    
    # 2. Check duplicate phone
    if candidate.phone or candidate.mobile_number:
        phone = candidate.phone or candidate.mobile_number
        dup_phone = await check_duplicate_phone(phone, db)
        if dup_phone and dup_phone.id != candidate.id:
            flags.append({
                "type": "duplicate_phone",
                "severity": "high",
                "message": f"Phone already exists for candidate: {dup_phone.full_name}",
                "existing_candidate_id": str(dup_phone.id)
            })
            fraud_score += 40
            is_duplicate = True
            fraud_reasons.append("Duplicate phone")
    
    # 3. Check duplicate resume hash
    if candidate.resume_hash:
        dup_hash = await check_duplicate_resume_hash(candidate.resume_hash, db)
        if dup_hash and dup_hash.id != candidate.id:
            flags.append({
                "type": "duplicate_resume",
                "severity": "high",
                "message": f"Exact same resume file already uploaded by: {dup_hash.full_name}",
                "existing_candidate_id": str(dup_hash.id)
            })
            fraud_score += 50
            is_duplicate = True
            fraud_reasons.append("Duplicate resume file")
    
    # 4. Check resume text similarity
    similar_resumes = await calculate_resume_similarity(candidate, db)
    if similar_resumes:
        for similar in similar_resumes:
            flags.append({
                "type": "similar_resume",
                "severity": "medium",
                "message": f"Resume {similar['similarity_score']}% similar to {similar['candidate_name']}",
                "existing_candidate_id": similar['candidate_id'],
                "similarity_score": similar['similarity_score']
            })
            fraud_score += 20
            is_duplicate = True
            fraud_reasons.append(f"Resume similarity: {similar['similarity_score']}%")
    
    # 5. Check experience inflation
    if candidate.experience_years and candidate.experience_years > 40:
        flags.append({
            "type": "inflated_experience",
            "severity": "high",
            "message": f"Unrealistic experience: {candidate.experience_years} years"
        })
        fraud_score += 30
        fraud_reasons.append("Inflated experience")
    
    # 6. Check skill padding
    if candidate.skills:
        skill_count = len(candidate.skills)
        exp_years = float(candidate.experience_years) if candidate.experience_years else 0
        
        if exp_years < 2 and skill_count > 15:
            flags.append({
                "type": "skill_padding",
                "severity": "medium",
                "message": f"Entry-level candidate with {skill_count} skills"
            })
            fraud_score += 15
            fraud_reasons.append("Skill padding")
        elif exp_years < 4 and skill_count > 25:
            flags.append({
                "type": "skill_padding",
                "severity": "medium",
                "message": f"Junior candidate with {skill_count} skills"
            })
            fraud_score += 15
            fraud_reasons.append("Skill padding")
    
    # 7. Check multiple applications
    if candidate.application_attempts and candidate.application_attempts > 3:
        flags.append({
            "type": "multiple_applications",
            "severity": "medium",
            "message": f"Applied {candidate.application_attempts} times"
        })
        fraud_score += 10
        fraud_reasons.append("Multiple applications")
    
    # 8. Check template resume patterns
    if candidate.resume_text:
        template_phrases = [
            "results-oriented professional",
            "highly motivated self-starter",
            "proven track record of success",
            "team player with excellent communication",
            "detail-oriented professional",
            "passionate about technology",
        ]
        text_lower = candidate.resume_text.lower()
        found_phrases = [p for p in template_phrases if p in text_lower]
        
        if len(found_phrases) >= 3:
            flags.append({
                "type": "template_resume",
                "severity": "low",
                "message": f"Resume contains {len(found_phrases)} generic template phrases",
                "phrases": found_phrases
            })
            fraud_score += 5
            fraud_reasons.append("Template resume")
    
    # Cap fraud score at 100
    fraud_score = min(100, fraud_score)
    
    # Determine if candidate should be flagged
    is_flagged = fraud_score >= 40 or is_duplicate
    
    fraud_reason = "; ".join(fraud_reasons) if fraud_reasons else None
    
    return {
        "fraud_score": fraud_score,
        "is_flagged": is_flagged,
        "is_duplicate": is_duplicate,
        "fraud_reason": fraud_reason,
        "flags": flags,
        "total_flags": len(flags)
    }


async def validate_candidate_pipeline(candidate: Candidate, db: AsyncSession) -> Dict:
    """
    Full validation pipeline for candidate integrity.
    
    Returns:
        {
            "validation_result": Dict,
            "recommendation": str,
            "should_block": bool
        }
    """
    validation_result = await calculate_fraud_score(candidate, db)
    
    fraud_score = validation_result["fraud_score"]
    is_duplicate = validation_result["is_duplicate"]
    
    # Determine recommendation
    if fraud_score >= 70 or is_duplicate:
        recommendation = "REJECT"
        should_block = True
    elif fraud_score >= 40:
        recommendation = "MANUAL_REVIEW"
        should_block = False
    else:
        recommendation = "APPROVE"
        should_block = False
    
    return {
        "validation_result": validation_result,
        "recommendation": recommendation,
        "should_block": should_block
    }


async def check_duplicate_candidate(
    email: str,
    mobile_number: str,
    db: AsyncSession
) -> Dict:
    """
    Check if candidate is duplicate based on email or phone.
    Used during basic details submission.
    """
    # Check email
    if email:
        dup_email = await check_duplicate_email(email, db)
        if dup_email:
            return {
                "is_duplicate": True,
                "match_type": "email",
                "existing_candidate_id": str(dup_email.id),
                "existing_candidate_name": dup_email.full_name
            }
    
    # Check phone
    if mobile_number:
        dup_phone = await check_duplicate_phone(mobile_number, db)
        if dup_phone:
            return {
                "is_duplicate": True,
                "match_type": "phone",
                "existing_candidate_id": str(dup_phone.id),
                "existing_candidate_name": dup_phone.full_name
            }
    
    return {
        "is_duplicate": False,
        "match_type": None,
        "existing_candidate_id": None
    }
