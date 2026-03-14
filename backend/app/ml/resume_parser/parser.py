"""
Resume parser — extracts structured data from resume text.
Uses regex + simple heuristics (no heavy ML dependency required).
"""

from __future__ import annotations

import re
from dataclasses import dataclass, asdict
from datetime import datetime
from typing import Any, Dict, List, Optional


# ──────────────────────────────────────────────
# Regex patterns
# ──────────────────────────────────────────────

EMAIL_RE = re.compile(r"[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+")
PHONE_RE = re.compile(r"[\+]?[\d\s\-().]{7,20}")

YEAR_RE = re.compile(r"\b(19|20)\d{2}\b")

DATE_RANGE_RE = re.compile(
    r"""
    (?P<start_month>[A-Za-z]{3,9})?      # optional start month
    \s*
    (?P<start_year>(19|20)\d{2})        # start year
    \s*(?:-|–|to)\s*
    (?:
        (?P<end_month>[A-Za-z]{3,9})?\s*
        (?P<end_year>(19|20)\d{2}|present|Present|PRESENT)
    )
    """,
    re.VERBOSE,
)


# ──────────────────────────────────────────────
# Skill dictionary
# ──────────────────────────────────────────────

SKILL_KEYWORDS: set[str] = {
    # Languages
    "python", "java", "javascript", "typescript", "c", "c++", "c#", "go", "rust",
    # Web / frameworks
    "react", "angular", "vue", "next.js", "node.js", "express", "django",
    "flask", "fastapi", "spring", "spring boot",
    # Databases
    "sql", "mysql", "postgresql", "mongodb", "redis",
    # Cloud / devops
    "docker", "kubernetes", "aws", "azure", "gcp", "terraform", "ci/cd",
    # ML / data
    "machine learning", "deep learning", "nlp", "pytorch", "tensorflow",
    "pandas", "numpy", "scikit-learn", "data science",
    # Tools
    "git", "linux", "jira", "power bi", "tableau",
    # Frontend
    "html", "css", "sass", "tailwind", "bootstrap",
    # Misc
    "graphql", "rest api", "microservices", "figma",
}

SPLIT_SEPARATORS_RE = re.compile(r"[,\u2022;|/•]+")


@dataclass
class EducationEntry:
    degree: str
    institution: str


# ──────────────────────────────────────────────
# Section detection
# ──────────────────────────────────────────────

SECTION_HEADERS = {
    "education": ["education", "academic history", "academics"],
    "skills": ["technical skills", "skills", "tech stack"],
    "experience": ["experience", "work experience", "professional experience", "employment"],
    "projects": ["projects", "personal projects", "academic projects"],
}


def _normalize_heading(line: str) -> str:
    return re.sub(r"[^a-z]", "", line.lower())


def split_sections(text: str) -> Dict[str, List[str]]:
    lines = [ln.strip() for ln in text.splitlines()]
    sections: Dict[str, List[str]] = {}
    current_key: Optional[str] = None

    for line in lines:
        norm = _normalize_heading(line)
        matched_key = None
        for key, headers in SECTION_HEADERS.items():
            for header in headers:
                if _normalize_heading(header) == norm:
                    matched_key = key
                    break
            if matched_key:
                break

        if matched_key:
            current_key = matched_key
            sections.setdefault(current_key, [])
            continue

        if current_key and line:
            sections.setdefault(current_key, []).append(line)

    return sections


# ──────────────────────────────────────────────
# Core extractors
# ──────────────────────────────────────────────

def extract_email(text: str) -> Optional[str]:
    match = EMAIL_RE.search(text)
    return match.group(0) if match else None


def extract_phone(text: str) -> Optional[str]:
    match = PHONE_RE.search(text)
    return match.group(0).strip() if match else None


def normalize_skill_token(token: str) -> str:
    token = token.strip().lower()
    replacements = {
        "nodejs": "node.js",
        "reactjs": "react",
        "js": "javascript",
        "ts": "typescript",
        "postgre": "postgresql",
    }
    return replacements.get(token, token)


def extract_skills_general(text: str) -> list[str]:
    """Keyword-based skill matching across full text."""
    text_lower = text.lower()
    found: set[str] = set()
    for skill in SKILL_KEYWORDS:
        if skill in text_lower:
            found.add(skill)
    return sorted(found)


def extract_skills_from_section(lines: list[str]) -> list[str]:
    found: set[str] = set()
    for line in lines:
        parts = SPLIT_SEPARATORS_RE.split(line)
        for part in parts:
            token = normalize_skill_token(part)
            if not token:
                continue
            for skill in SKILL_KEYWORDS:
                if skill in token or token in skill:
                    found.add(skill)
    return sorted(found)


def extract_education(lines: list[str]) -> list[dict[str, str]]:
    DEGREE_KEYWORDS = [
        "b.tech", "btech", "b.e", "be", "bsc", "b.sc", "bachelor",
        "m.tech", "mtech", "m.e", "me", "msc", "m.sc", "master",
        "mba", "phd", "doctorate",
    ]

    edu_entries: list[EducationEntry] = []

    for i, line in enumerate(lines):
        low = line.lower()
        if any(kw in low for kw in DEGREE_KEYWORDS):
            degree = line.strip()
            institution = ""
            parts = re.split(r"[-,|]", line, maxsplit=1)
            if len(parts) > 1:
                institution = parts[1].strip()
            elif i + 1 < len(lines):
                institution = lines[i + 1].strip()

            edu_entries.append(
                EducationEntry(
                    degree=degree[:80],
                    institution=(institution or "Unknown")[:80],
                )
            )

    return [asdict(e) for e in edu_entries]


def _month_to_number(name: Optional[str]) -> int:
    if not name:
        return 1
    name = name[:3].lower()
    mapping = {
        "jan": 1, "feb": 2, "mar": 3, "apr": 4, "may": 5, "jun": 6,
        "jul": 7, "aug": 8, "sep": 9, "oct": 10, "nov": 11, "dec": 12,
    }
    return mapping.get(name, 1)


def extract_experience_years_from_lines(lines: list[str]) -> float:
    now = datetime.utcnow()
    total_months = 0

    for line in lines:
        for match in DATE_RANGE_RE.finditer(line):
            start_year = int(match.group("start_year"))
            start_month = _month_to_number(match.group("start_month"))

            end_year_raw = match.group("end_year")
            if end_year_raw is None or "present" in end_year_raw.lower():
                end_year = now.year
                end_month = now.month
            else:
                end_year = int(end_year_raw)
                end_month = _month_to_number(match.group("end_month"))

            start_total = start_year * 12 + start_month
            end_total = end_year * 12 + end_month
            if end_total >= start_total:
                total_months += end_total - start_total

    if total_months == 0:
        exp_match = re.search(
            r"(\d+(?:\.\d+)?)\s*(?:\+)?\s*(?:years?|yrs?)\s*(?:of)?\s*experience",
            "\n".join(lines),
            flags=re.IGNORECASE,
        )
        if exp_match:
            return float(exp_match.group(1))

    return round(total_months / 12.0, 2) if total_months > 0 else 0.0


def parse_resume(text: str) -> dict[str, Any]:
    """Full resume parsing pipeline."""
    email = extract_email(text)
    phone = extract_phone(text)
    sections = split_sections(text)

    skills: set[str] = set(extract_skills_general(text))
    if "skills" in sections:
        skills.update(extract_skills_from_section(sections["skills"]))
    normalized_skills = sorted({s.lower() for s in skills})

    education: list[dict[str, str]] = []
    if "education" in sections:
        education = extract_education(sections["education"])

    experience_years = 0.0
    if "experience" in sections:
        experience_years = extract_experience_years_from_lines(sections["experience"])

    return {
        "email": email,
        "phone": phone,
        "skills": normalized_skills,
        "education": education,
        "experience_years": experience_years,
        "raw_length": len(text),
    }
