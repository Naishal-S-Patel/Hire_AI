"""
AI summary generator — produces a concise 3-line candidate summary.

Uses OpenAI GPT when an API key is available, falls back to a heuristic summary.
"""

from __future__ import annotations

from typing import Any

from app.config import settings


def _heuristic_summary(candidate_data: dict[str, Any]) -> str:
    """Fallback summary built from structured data."""
    name = candidate_data.get("full_name", "Candidate")
    skills = candidate_data.get("skills", [])
    exp = candidate_data.get("experience_years")
    location = candidate_data.get("location", "")

    line1 = f"{name} is a professional"
    if exp:
        line1 += f" with {exp} years of experience"
    line1 += "."

    line2 = f"Key skills include {', '.join(skills[:5])}." if skills else "Skills information not available."

    line3 = f"Based in {location}." if location else "Location not specified."

    return f"{line1}\n{line2}\n{line3}"


async def generate_summary(candidate_data: dict[str, Any]) -> str:
    """
    Generate a 3-line AI summary for a candidate.

    Attempts OpenAI GPT first; falls back to heuristic if no API key.
    """
    if not settings.OPENAI_API_KEY or settings.OPENAI_API_KEY.startswith("sk-placeholder"):
        return _heuristic_summary(candidate_data)

    try:
        from openai import AsyncOpenAI

        client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
        prompt = (
            "You are an expert recruiter. Write exactly 3 concise lines summarizing this candidate:\n"
            f"Name: {candidate_data.get('full_name', 'N/A')}\n"
            f"Skills: {', '.join(candidate_data.get('skills', []))}\n"
            f"Experience: {candidate_data.get('experience_years', 'N/A')} years\n"
            f"Location: {candidate_data.get('location', 'N/A')}\n"
            f"Education: {candidate_data.get('education', 'N/A')}\n"
        )
        response = await client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=200,
            temperature=0.5,
        )
        return response.choices[0].message.content.strip()
    except Exception:
        return _heuristic_summary(candidate_data)
