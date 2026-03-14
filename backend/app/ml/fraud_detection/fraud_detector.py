"""
Fraud detection module — detects timeline gaps and inflated experience.
"""

from __future__ import annotations

import re
from datetime import datetime
from typing import Any

CURRENT_YEAR = datetime.now().year


def detect_timeline_gaps(resume_text: str, education: list[dict], experience_years: float | None) -> list[dict[str, Any]]:
    """Detect suspicious gaps — works from raw resume text since education is often unparsed."""
    flags: list[dict[str, Any]] = []

    if not experience_years:
        return flags

    # Flag absurdly high experience
    if experience_years > 40:
        flags.append({
            "type": "inflated_experience",
            "severity": "high",
            "message": f"Stated experience ({experience_years} years) exceeds reasonable threshold.",
        })

    # Check education years from parsed education list
    recent_years = [str(y) for y in range(2018, CURRENT_YEAR + 1)]
    for edu in (education or []):
        degree_text = str(edu).lower()
        if any(yr in degree_text for yr in recent_years) and experience_years > 8:
            flags.append({
                "type": "timeline_inconsistency",
                "severity": "medium",
                "message": f"Recent degree detected but {experience_years} years of experience claimed.",
            })
            break

    # Also scan raw resume text for graduation years
    if not any(f["type"] == "timeline_inconsistency" for f in flags):
        grad_pattern = r'\b(20(?:1[5-9]|2[0-4]))\b'
        years_in_text = [int(y) for y in re.findall(grad_pattern, resume_text)]
        if years_in_text:
            most_recent_year = max(years_in_text)
            # Max possible experience = current year - graduation year
            max_possible = CURRENT_YEAR - most_recent_year
            if experience_years > max_possible + 2:  # +2 tolerance
                flags.append({
                    "type": "timeline_inconsistency",
                    "severity": "medium",
                    "message": (
                        f"Claims {experience_years} years experience but most recent year "
                        f"found ({most_recent_year}) allows max ~{max_possible} years."
                    ),
                })

    return flags


def detect_inflated_skills(skills: list[str], experience_years: float | None) -> list[dict[str, Any]]:
    """Flag candidates with too many skills relative to experience."""
    flags: list[dict[str, Any]] = []

    if not experience_years:
        experience_years = 0

    skill_count = len(skills)

    if experience_years < 2 and skill_count > 12:
        flags.append({
            "type": "inflated_skills",
            "severity": "medium",
            "message": f"Entry-level candidate ({experience_years} yrs) listing {skill_count} skills — possible padding.",
        })
    elif experience_years < 4 and skill_count > 20:
        flags.append({
            "type": "inflated_skills",
            "severity": "medium",
            "message": f"Junior candidate ({experience_years} yrs) listing {skill_count} skills — possible padding.",
        })

    return flags


def detect_duplicate_content(text: str) -> list[dict[str, Any]]:
    """Detect copy-paste / template resume patterns."""
    flags: list[dict[str, Any]] = []
    template_phrases = [
        "results-oriented professional",
        "highly motivated self-starter",
        "proven track record of success",
        "team player with excellent communication",
        "detail-oriented professional",
        "passionate about technology",
    ]
    text_lower = text.lower()
    found = [p for p in template_phrases if p in text_lower]
    if len(found) >= 2:
        flags.append({
            "type": "template_resume",
            "severity": "low",
            "message": f"Resume contains {len(found)} generic template phrases.",
            "phrases": found,
        })
    return flags


def run_fraud_detection(
    resume_text: str,
    skills: list[str],
    experience_years: float | None,
    education: list[dict[str, str]],
) -> dict[str, Any]:
    """Full fraud detection pipeline. Returns risk_score (0-100) and flags."""
    all_flags: list[dict[str, Any]] = []
    all_flags.extend(detect_timeline_gaps(resume_text, education, experience_years))
    all_flags.extend(detect_inflated_skills(skills, experience_years))
    all_flags.extend(detect_duplicate_content(resume_text))

    severity_weights = {"high": 40, "medium": 20, "low": 10}
    risk_score = min(sum(severity_weights.get(f["severity"], 5) for f in all_flags), 100)

    if risk_score >= 40:
        risk_level = "HIGH"
    elif risk_score >= 15:
        risk_level = "MEDIUM"
    else:
        risk_level = "LOW"

    return {
        "risk_score": risk_score,
        "risk_level": risk_level,
        "flags": all_flags,
        "total_flags": len(all_flags),
    }
