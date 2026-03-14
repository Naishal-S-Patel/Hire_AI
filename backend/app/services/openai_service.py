"""
OpenAI service for generating AI-powered candidate summaries.
"""

import logging
from typing import List, Optional

import httpx

from app.config import settings

logger = logging.getLogger(__name__)


async def generate_ai_summary(
    resume_text: str,
    skills: List[str],
    experience_years: float,
    name: Optional[str] = None
) -> Optional[str]:
    """
    Generate AI-powered executive summary using OpenAI GPT-4.1-mini.
    
    Args:
        resume_text: Full text extracted from resume
        skills: List of candidate skills
        experience_years: Years of experience
        name: Candidate name (optional)
    
    Returns:
        AI-generated summary or None if API call fails
    """
    
    if not settings.OPENAI_API_KEY or settings.OPENAI_API_KEY == "sk-placeholder":
        logger.error("OpenAI API key not configured")
        return None
    
    # Prepare context for OpenAI
    skills_text = ", ".join(skills[:10]) if skills else "various technologies"
    exp_text = f"{experience_years} years" if experience_years > 0 else "entry-level"
    
    # Construct prompt
    prompt = f"""Generate a short recruiter-friendly executive summary for this candidate.

Candidate Information:
- Name: {name or "Candidate"}
- Experience Level: {exp_text}
- Key Technologies: {skills_text}
- Resume Excerpt: {resume_text[:800]}

Requirements:
- 2-3 sentences maximum
- Include experience level, key technologies, and candidate strengths
- Professional and concise tone
- Focus on technical capabilities and problem-solving skills

Example format:
"[Name] is a [role] specializing in [technologies]. They have experience in [domains] and demonstrate strong [skills]."
"""
    
    try:
        logger.info(f"Calling OpenAI API for summary generation (experience: {exp_text})")
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                "https://api.openai.com/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {settings.OPENAI_API_KEY}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": "gpt-4o-mini",  # Using gpt-4o-mini (latest efficient model)
                    "messages": [
                        {
                            "role": "system",
                            "content": "You are a professional recruiter assistant. Generate concise, impactful candidate summaries that highlight technical expertise and professional strengths."
                        },
                        {
                            "role": "user",
                            "content": prompt
                        }
                    ],
                    "max_tokens": 200,
                    "temperature": 0.7,
                }
            )
            
            response.raise_for_status()
            data = response.json()
            
            summary = data["choices"][0]["message"]["content"].strip()
            logger.info(f"OpenAI summary generated successfully: {summary[:50]}...")
            
            return summary
            
    except httpx.HTTPStatusError as e:
        logger.error(f"OpenAI API HTTP error: {e.response.status_code} - {e.response.text}")
        return None
    except httpx.TimeoutException:
        logger.error("OpenAI API request timed out")
        return None
    except Exception as e:
        logger.error(f"OpenAI API error: {str(e)}")
        return None


async def regenerate_summary_for_candidate(
    candidate_id: str,
    resume_text: str,
    skills: List[str],
    experience_years: float,
    name: str
) -> Optional[str]:
    """
    Regenerate AI summary for an existing candidate.
    
    This is useful for:
    - Updating summaries for candidates with static templates
    - Regenerating after resume updates
    - Batch processing existing candidates
    """
    logger.info(f"Regenerating AI summary for candidate: {candidate_id}")
    
    summary = await generate_ai_summary(
        resume_text=resume_text,
        skills=skills,
        experience_years=experience_years,
        name=name
    )
    
    if summary:
        logger.info(f"Successfully regenerated summary for candidate {candidate_id}")
    else:
        logger.error(f"Failed to regenerate summary for candidate {candidate_id}")
    
    return summary
