"""
Script to calculate and update ATS scores for all existing candidates.
Run this to backfill ATS scores based on profile completeness.

Usage:
    python update_ats_scores.py
"""

import asyncio
from sqlalchemy import select
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

from app.config import settings
from app.models.candidate import Candidate


def calculate_ats_score(candidate):
    """Calculate ATS score based on profile completeness."""
    score = 0
    
    # Basic info (30 points)
    if candidate.full_name and candidate.full_name != "Unknown":
        score += 10
    if candidate.email and "placeholder" not in candidate.email:
        score += 10
    if candidate.phone:
        score += 10
    
    # Professional info (40 points)
    if candidate.location:
        score += 8
    if candidate.experience_years:
        exp_years = int(candidate.experience_years) if candidate.experience_years else 0
        score += min(15, exp_years * 2)
    if candidate.skills:
        skill_count = len(candidate.skills)
        score += min(17, skill_count * 2)
    
    # Additional data (30 points)
    if candidate.education and len(candidate.education) > 0:
        score += 10
    if candidate.ai_summary and candidate.ai_summary != "":
        score += 10
    if candidate.parsed_json and len(candidate.parsed_json) > 3:
        score += 10
    
    return min(100, score)


async def update_ats_scores():
    """Update ATS scores for all candidates."""
    
    # Create async engine
    engine = create_async_engine(settings.DATABASE_URL, echo=True)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    
    async with async_session() as db:
        # Fetch all candidates
        result = await db.execute(select(Candidate))
        candidates = result.scalars().all()
        
        print(f"\n{'='*60}")
        print(f"Found {len(candidates)} candidates")
        print(f"{'='*60}\n")
        
        if len(candidates) == 0:
            print("✅ No candidates found!")
            return
        
        updated_count = 0
        skipped_count = 0
        
        for i, candidate in enumerate(candidates, 1):
            try:
                # Calculate new ATS score
                new_score = calculate_ats_score(candidate)
                old_score = candidate.ats_score or 0
                
                # Update if different
                if new_score != old_score:
                    candidate.ats_score = new_score
                    await db.flush()
                    print(f"[{i}/{len(candidates)}] {candidate.full_name}: {old_score} → {new_score}")
                    updated_count += 1
                else:
                    print(f"[{i}/{len(candidates)}] {candidate.full_name}: {old_score} (no change)")
                    skipped_count += 1
                    
            except Exception as e:
                print(f"[{i}/{len(candidates)}] ❌ Error for {candidate.full_name}: {str(e)}")
                skipped_count += 1
        
        # Commit all changes
        await db.commit()
        
        # Calculate average
        total_score = sum(c.ats_score or 0 for c in candidates)
        avg_score = total_score / len(candidates) if len(candidates) > 0 else 0
        
        print(f"\n{'='*60}")
        print(f"ATS Score Update Complete!")
        print(f"{'='*60}")
        print(f"✅ Updated: {updated_count}")
        print(f"⏭️  Skipped: {skipped_count}")
        print(f"📊 Total: {len(candidates)}")
        print(f"📈 Average ATS Score: {avg_score:.1f}/100")
        print(f"{'='*60}\n")


if __name__ == "__main__":
    print("\n🚀 Starting ATS Score Calculation for All Candidates...\n")
    asyncio.run(update_ats_scores())
    print("✨ Done!\n")
