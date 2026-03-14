import asyncio
from app.db import engine
from sqlalchemy import text

async def check():
    async with engine.connect() as conn:
        result = await conn.execute(text(
            "SELECT column_name FROM information_schema.columns WHERE table_name='candidates' ORDER BY ordinal_position"
        ))
        cols = [r[0] for r in result]
        print("DB columns:", cols)
        
        missing = []
        needed = ['is_duplicate', 'fraud_score', 'fraud_reason', 'application_attempts', 'is_flagged', 'verification_status', 'status', 'first_name', 'last_name', 'mobile_number', 'place_of_residence', 'confidence_score', 'technical_score', 'video_screening_completed', 'canonical_id']
        for col in needed:
            if col not in cols:
                missing.append(col)
        print("Missing columns:", missing)

asyncio.run(check())
