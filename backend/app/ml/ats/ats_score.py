"""
ATS scoring — compares a job description against a resume using cosine similarity.
"""

from __future__ import annotations

from typing import Any

import numpy as np
from sklearn.metrics.pairwise import cosine_similarity

from app.ml.embeddings.embedder import encode_text


def compute_ats_score(resume_text: str, job_description: str) -> dict[str, Any]:
    """
    Compute an ATS compatibility score between a resume and a job description.

    Returns a dict with overall score (0-100), skill overlap info, and keyword matches.
    """
    resume_vec = np.array(encode_text(resume_text)).reshape(1, -1)
    jd_vec = np.array(encode_text(job_description)).reshape(1, -1)

    similarity = float(cosine_similarity(resume_vec, jd_vec)[0][0])
    score = round(similarity * 100, 2)

    # Keyword overlap heuristic
    resume_tokens = set(resume_text.lower().split())
    jd_tokens = set(job_description.lower().split())
    common = resume_tokens & jd_tokens
    keyword_score = round(len(common) / max(len(jd_tokens), 1) * 100, 2)

    return {
        "ats_score": score,
        "semantic_similarity": round(similarity, 4),
        "keyword_overlap_score": keyword_score,
        "matched_keywords": sorted(list(common))[:50],
        "total_jd_keywords": len(jd_tokens),
        "total_resume_keywords": len(resume_tokens),
    }
