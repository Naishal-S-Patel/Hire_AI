"""
Script to generate AI summaries for all candidates that don't have one.
Run this to backfill summaries for existing candidates.

Usage:
    python generate_missing_summaries.py
"""

import asyncio
import httpx
from sqlalchemy import select
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

from app.config import settings
from app.models.candidate import Candidate


async def generate_summaries():
    """Generate summaries for all candidates without one."""
    
    # Create async engine
    engine = create_async_engine(settings.DATABASE_URL, echo=True)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    
    async with async_session() as db:
        # Fetch all candidates without summaries
        result = await db.execute(
            select(Candidate).where(
                (Candidate.ai_summary == None) | (Candidate.ai_summary == "")
            )
        )
        candidates = result.scalars().all()
        
        print(f"\n{'='*60}")
        print(f"Found {len(candidates)} candidates without AI summaries")
        print(f"{'='*60}\n")
        
        if len(candidates) == 0:
            print("✅ All candidates already have summaries!")
            return
        
        success_count = 0
        fail_count = 0
        
        async with httpx.AsyncClient(timeout=60) as client:
            for i, candidate in enumerate(candidates, 1):
                try:
                    print(f"[{i}/{len(candidates)}] Processing: {candidate.full_name}")
                    
                    # Skip if no skills
                    if not candidate.skills or len(candidate.skills) == 0:
                        print(f"  ⚠️  Skipped - No skills found")
                        fail_count += 1
                        continue
                    
                    # Prepare data
                    name = candidate.full_name
                    experience = int(candidate.experience_years) if candidate.experience_years else 0
                    skills = candidate.skills
                    
                    # Call ML service
                    params = {"name": name, "experience": experience}
                    form_data = [("skills", skill) for skill in skills]
                    
                    ml_resp = await client.post(
                        f"{settings.ML_SERVICE_URL}/ml/v1/summary",
                        params=params,
                        data=form_data
                    )
                    
                    if ml_resp.status_code == 200:
                        ml_result = ml_resp.json()
                        summary = ml_result.get("summary", "")
                        
                        # Update candidate
                        candidate.ai_summary = summary
                        await db.flush()
                        
                        print(f"  ✅ Generated summary: {summary[:80]}...")
                        success_count += 1
                    else:
                        print(f"  ❌ ML service error: {ml_resp.status_code}")
                        fail_count += 1
                        
                except Exception as e:
                    print(f"  ❌ Error: {str(e)}")
                    fail_count += 1
                
                # Small delay to avoid overwhelming the ML service
                await asyncio.sleep(0.5)
        
        # Commit all changes
        await db.commit()
        
        print(f"\n{'='*60}")
        print(f"Summary Generation Complete!")
        print(f"{'='*60}")
        print(f"✅ Success: {success_count}")
        print(f"❌ Failed: {fail_count}")
        print(f"📊 Total: {len(candidates)}")
        print(f"{'='*60}\n")


if __name__ == "__main__":
    print("\n🚀 Starting AI Summary Generation for Existing Candidates...\n")
    asyncio.run(generate_summaries())
    print("✨ Done!\n")
