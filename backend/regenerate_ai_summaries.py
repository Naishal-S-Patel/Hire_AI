"""
Script to regenerate AI summaries for all existing candidates.
Run this to replace static template summaries with OpenAI-generated ones.
"""

import asyncio
import logging
import sys
from sqlalchemy import select
from app.db import async_session_maker
from app.models.candidate import Candidate
from app.services.openai_service import generate_ai_summary

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def regenerate_all_summaries():
    """Regenerate AI summaries for all candidates."""
    
    async with async_session_maker() as db:
        # Fetch all candidates
        result = await db.execute(select(Candidate))
        candidates = result.scalars().all()
        
        logger.info(f"Found {len(candidates)} candidates")
        
        success_count = 0
        failed_count = 0
        skipped_count = 0
        
        for i, candidate in enumerate(candidates, 1):
            logger.info(f"Processing {i}/{len(candidates)}: {candidate.full_name}")
            
            # Skip if no resume text
            if not candidate.resume_text:
                logger.warning(f"  Skipping - no resume text")
                skipped_count += 1
                continue
            
            # Generate new summary
            summary = await generate_ai_summary(
                resume_text=candidate.resume_text,
                skills=candidate.skills or [],
                experience_years=float(candidate.experience_years or 0),
                name=candidate.full_name
            )
            
            if summary:
                old_summary = candidate.ai_summary
                candidate.ai_summary = summary
                logger.info(f"  ✓ Generated: {summary[:80]}...")
                if old_summary:
                    logger.info(f"  Old: {old_summary[:80]}...")
                success_count += 1
            else:
                logger.error(f"  ✗ Failed to generate summary")
                failed_count += 1
        
        # Commit all changes
        await db.commit()
        
        logger.info("\n" + "="*60)
        logger.info("SUMMARY REGENERATION COMPLETE")
        logger.info("="*60)
        logger.info(f"Total candidates: {len(candidates)}")
        logger.info(f"✓ Success: {success_count}")
        logger.info(f"✗ Failed: {failed_count}")
        logger.info(f"⊘ Skipped (no resume text): {skipped_count}")
        logger.info("="*60)


if __name__ == "__main__":
    print("\n" + "="*60)
    print("AI SUMMARY REGENERATION SCRIPT")
    print("="*60)
    print("\nThis will regenerate AI summaries for ALL candidates using OpenAI.")
    print("Make sure OPENAI_API_KEY is configured in backend/.env")
    print("\nPress Ctrl+C to cancel, or Enter to continue...")
    
    try:
        input()
    except KeyboardInterrupt:
        print("\nCancelled.")
        sys.exit(0)
    
    asyncio.run(regenerate_all_summaries())
