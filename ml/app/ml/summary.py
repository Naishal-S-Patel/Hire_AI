import os
import logging
from openai import OpenAI

logger = logging.getLogger(__name__)
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY", ""))

def generate_summary(name, experience, skills):
    """
    Generate a professional AI summary for a candidate using GPT-4o-mini.
    
    Args:
        name: Candidate's full name
        experience: Years of experience
        skills: List of skills
    
    Returns:
        Professional summary string or fallback summary if OpenAI fails
    """
    if not skills:
        logger.warning(f"No skills provided for {name}, returning basic summary")
        return f"{name} is a professional with {experience} years of experience in their field."
    
    # Check if API key is configured
    if not client.api_key or client.api_key == "":
        logger.warning("OpenAI API key not configured - using fallback summary")
        return _generate_fallback_summary(name, experience, skills)
    
    try:
        logger.info(f"Generating AI summary for {name} using GPT-4o-mini")
        
        # Categorize skills for better summary
        top_skills = skills[:10]  # Use top 10 skills
        skill_list = ", ".join(top_skills)
        
        # Determine seniority level
        if experience >= 10:
            seniority = "senior"
            level_desc = "seasoned"
        elif experience >= 5:
            seniority = "experienced"
            level_desc = "skilled"
        elif experience >= 2:
            seniority = "mid-level"
            level_desc = "capable"
        else:
            seniority = "emerging"
            level_desc = "motivated"
        
        # Detect primary domain from skills
        domain = _detect_domain(top_skills)
        
        # Create a detailed prompt for better summaries
        prompt = f"""Write a compelling 2-3 sentence professional summary for this candidate. Use third person.

Candidate: {name}
Experience: {experience} years ({seniority} level)
Domain: {domain}
Key Skills: {skill_list}

Write a summary that:
1. Opens with their professional identity and domain expertise
2. Highlights their experience level and technical strengths
3. Emphasizes their value and impact potential
4. Uses confident, action-oriented language
5. Avoids generic phrases like "skilled professional" or "team player"
6. Sounds compelling to technical recruiters

Be specific, concise, and impactful. Focus on what makes them valuable."""

        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {
                    "role": "system", 
                    "content": "You are an expert technical recruiter. Write compelling, specific professional summaries that highlight technical expertise and value. Be concise but impactful. Avoid clichés."
                },
                {
                    "role": "user", 
                    "content": prompt
                }
            ],
            max_tokens=250,
            temperature=0.75,
            presence_penalty=0.4,
            frequency_penalty=0.4
        )
        
        summary = response.choices[0].message.content.strip()
        summary = summary.strip('"').strip("'")
        
        logger.info(f"✓ Generated AI summary for {name}")
        return summary
        
    except Exception as e:
        logger.error(f"OpenAI API error: {e}")
        return _generate_fallback_summary(name, experience, skills)


def _detect_domain(skills):
    """Detect primary technical domain from skills."""
    skills_lower = [s.lower() for s in skills]
    
    # Domain detection patterns
    if any(s in skills_lower for s in ['react', 'vue', 'angular', 'frontend', 'css', 'html']):
        return "Frontend Development"
    elif any(s in skills_lower for s in ['node', 'django', 'flask', 'fastapi', 'backend', 'api']):
        return "Backend Development"
    elif any(s in skills_lower for s in ['react', 'node', 'fullstack', 'full-stack', 'full stack']):
        return "Full-Stack Development"
    elif any(s in skills_lower for s in ['ml', 'machine learning', 'ai', 'deep learning', 'tensorflow', 'pytorch']):
        return "Machine Learning & AI"
    elif any(s in skills_lower for s in ['data', 'analytics', 'pandas', 'numpy', 'sql', 'tableau']):
        return "Data Science & Analytics"
    elif any(s in skills_lower for s in ['devops', 'docker', 'kubernetes', 'aws', 'azure', 'cloud']):
        return "DevOps & Cloud"
    elif any(s in skills_lower for s in ['mobile', 'android', 'ios', 'react native', 'flutter']):
        return "Mobile Development"
    elif any(s in skills_lower for s in ['qa', 'testing', 'selenium', 'automation']):
        return "Quality Assurance"
    else:
        return "Software Development"


def _generate_fallback_summary(name, experience, skills):
    """Generate a rule-based summary when OpenAI is unavailable."""
    domain = _detect_domain(skills)
    top_skills = skills[:5]
    
    if experience >= 10:
        level = "seasoned"
        descriptor = "extensive expertise"
    elif experience >= 5:
        level = "experienced"
        descriptor = "strong proficiency"
    elif experience >= 2:
        level = "skilled"
        descriptor = "solid foundation"
    else:
        level = "emerging"
        descriptor = "growing expertise"
    
    skill_text = ", ".join(top_skills[:3])
    
    summary = f"{name} is a {level} professional in {domain} with {experience} years of experience. "
    summary += f"Demonstrates {descriptor} in {skill_text}"
    
    if len(top_skills) > 3:
        summary += f", and {len(top_skills) - 3}+ other technologies"
    
    summary += f". Brings technical depth and problem-solving capabilities to deliver impactful solutions."
    
    return summary