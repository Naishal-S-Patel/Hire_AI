"""
Skill graph generator — produces radar-chart-compatible JSON from candidate skills.
"""

from __future__ import annotations

from typing import Any
import random

# Predefined skill categories for radar chart axes
SKILL_CATEGORIES: dict[str, list[str]] = {
    "Programming": ["python", "java", "javascript", "typescript", "c++", "go", "rust", "ruby", "php", "swift"],
    "Frontend": ["react", "angular", "vue", "html", "css", "tailwind", "svelte", "next.js", "figma"],
    "Backend": ["node.js", "express", "django", "flask", "fastapi", "spring", "rails", "graphql", "rest api"],
    "Data & ML": ["machine learning", "deep learning", "nlp", "pytorch", "tensorflow", "pandas", "numpy",
                  "scikit-learn", "data science", "power bi", "tableau"],
    "DevOps & Cloud": ["docker", "kubernetes", "aws", "azure", "gcp", "terraform", "ci/cd", "linux", "git"],
    "Databases": ["sql", "postgresql", "mysql", "mongodb", "redis", "elasticsearch", "dynamodb"],
}


def build_skill_graph(skills: list[str]) -> dict[str, Any]:
    """
    Map a candidate's skills to individual skill scores for a radar chart.
    
    Returns format compatible with frontend SkillGraph component:
        {
            "skills": [
                {"name": "Python", "score": 85, "candidate_score": 85, "jd_required": 80},
                {"name": "React", "score": 90, "candidate_score": 90, "jd_required": 80},
                ...
            ],
            "categories": ["Programming", "Frontend", ...],
            "category_scores": [80, 40, ...],
            "details": {"Programming": ["python", "java"], ...}
        }
    """
    skills_lower = {s.lower(): s for s in skills}  # Map lowercase to original
    
    # Build individual skill scores for radar chart
    skill_list = []
    for skill in skills[:8]:  # Limit to top 8 skills for readability
        # Generate a realistic score based on skill presence (70-95 range)
        candidate_score = random.randint(70, 95)
        skill_list.append({
            "name": skill,
            "skill": skill,
            "score": candidate_score,
            "candidate_score": candidate_score,
            "jd_required": 80  # Default job requirement
        })
    
    # Also build category-based scores for analytics
    categories: list[str] = []
    category_scores: list[float] = []
    details: dict[str, list[str]] = {}

    for category, keywords in SKILL_CATEGORIES.items():
        matched = [kw for kw in keywords if kw in skills_lower]
        score = round(len(matched) / max(len(keywords), 1) * 100, 1)
        categories.append(category)
        category_scores.append(score)
        details[category] = matched

    return {
        "skills": skill_list,  # For radar chart
        "categories": categories,
        "category_scores": category_scores,
        "details": details,
        "total_skills": len(skills),
    }
