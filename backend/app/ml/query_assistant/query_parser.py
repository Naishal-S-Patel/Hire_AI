"""
AI query assistant — converts natural-language queries to structured filters.

Uses LangChain + OpenAI when available; falls back to regex-based parsing.
"""

from __future__ import annotations

import re
from typing import Any

from app.config import settings


def _regex_parse(query: str) -> dict[str, Any]:
    """Heuristic NL → structured filter parser (no LLM required)."""
    filters: dict[str, Any] = {}
    q = query.lower()

    # Experience extraction
    exp_match = re.search(r"(\d+)\+?\s*(?:years?|yrs?)\s*(?:of\s*)?(?:experience)?", q)
    if exp_match:
        filters["min_experience"] = int(exp_match.group(1))

    # Location extraction
    loc_patterns = [
        r"(?:in|from|based in|located in|at)\s+([a-zA-Z\s]+?)(?:\s+with|\s+and|\s*$|,)",
    ]
    for pat in loc_patterns:
        loc_match = re.search(pat, q)
        if loc_match:
            filters["location"] = loc_match.group(1).strip().title()
            break

    # Skill extraction (common skills)
    common_skills = [
        "python", "java", "javascript", "react", "angular", "vue",
        "node.js", "django", "flask", "fastapi", "docker", "kubernetes",
        "aws", "azure", "gcp", "sql", "mongodb", "machine learning",
        "deep learning", "nlp", "pytorch", "tensorflow", "typescript",
    ]
    found_skills = [s for s in common_skills if s in q]
    if found_skills:
        filters["skills"] = found_skills

    return filters


async def parse_query(query: str) -> dict[str, Any]:
    """
    Parse a natural-language recruiting query into structured filters.

    Uses OpenAI/LangChain when available; regex fallback otherwise.
    """
    if not settings.OPENAI_API_KEY or settings.OPENAI_API_KEY.startswith("sk-placeholder"):
        return {
            "original_query": query,
            "parsed_filters": _regex_parse(query),
            "method": "regex",
        }

    try:
        from openai import AsyncOpenAI
        import json

        client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
        prompt = (
            "You are a recruiting search query parser. Convert the following natural language query "
            "into a JSON object with these possible fields: skills (list), min_experience (int), "
            "max_experience (int), location (str), education (str), job_title (str).\n\n"
            "Only include fields that are explicitly or implicitly mentioned.\n\n"
            f"Query: {query}\n\n"
            "Return ONLY valid JSON, no explanation."
        )
        response = await client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=300,
            temperature=0,
        )
        raw = response.choices[0].message.content.strip()
        parsed = json.loads(raw)
        return {
            "original_query": query,
            "parsed_filters": parsed,
            "method": "llm",
        }
    except Exception:
        return {
            "original_query": query,
            "parsed_filters": _regex_parse(query),
            "method": "regex_fallback",
        }
