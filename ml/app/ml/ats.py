import re
from sklearn.metrics.pairwise import cosine_similarity
from .embeddings import create_embedding


# Skill alias dictionary for normalization
SKILL_ALIASES = {
    # Programming Languages
    "py": "python",
    "js": "javascript",
    "ts": "typescript",
    
    # Frameworks & Libraries
    "nodejs": "node.js",
    "node": "node.js",
    "reactjs": "react",
    "vuejs": "vue",
    "springboot": "spring boot",
    
    # Data Science & ML
    "ml": "machine learning",
    "dl": "deep learning",
    "ai": "artificial intelligence",
    "tf": "tensorflow",
    "np": "numpy",
    "pd": "pandas",
    "sklearn": "scikit-learn",
    
    # Databases
    "postgres": "postgresql",
    "mongo": "mongodb",
    "db": "database",
    
    # DevOps & Cloud
    "k8s": "kubernetes",
    "docker": "docker",
    "ci": "ci/cd",
    "cd": "ci/cd",
    
    # Other
    "api": "rest api",
    "gql": "graphql",
    "css3": "css",
    "html5": "html"
}


def normalize_text(text):
    """
    Normalize text by replacing skill aliases with canonical names.
    
    Args:
        text: Input text (job description or resume)
    
    Returns:
        Normalized text with aliases replaced
    """
    if not text:
        return ""
    
    # Convert to lowercase
    normalized = text.lower()
    
    # Replace aliases with canonical names
    # Sort by length (descending) to handle longer aliases first
    for alias, canonical in sorted(SKILL_ALIASES.items(), key=lambda x: len(x[0]), reverse=True):
        # Use word boundaries to avoid partial matches
        pattern = r'\b' + re.escape(alias) + r'\b'
        normalized = re.sub(pattern, canonical, normalized)
    
    return normalized


def extract_skills_from_text(text, skill_list):
    """
    Extract skills mentioned in text from a given skill list.
    
    Args:
        text: Text to search for skills
        skill_list: List of skills to look for
    
    Returns:
        List of skills found in text
    """
    if not text or not skill_list:
        return []
    
    text_lower = text.lower()
    found_skills = []
    
    for skill in skill_list:
        skill_lower = skill.lower()
        # Check if skill appears in text (word boundary aware)
        pattern = r'\b' + re.escape(skill_lower) + r'\b'
        if re.search(pattern, text_lower):
            found_skills.append(skill)
    
    return found_skills


def ats_score(resume_text, jd_text):
    """
    Calculate ATS score between resume and job description.
    
    Normalizes text using skill aliases before computing similarity.
    
    Args:
        resume_text: Candidate resume text
        jd_text: Job description text
    
    Returns:
        ATS score (0-100) representing similarity
    """
    # Normalize both texts
    normalized_resume = normalize_text(resume_text)
    normalized_jd = normalize_text(jd_text)
    
    # Create embeddings from normalized text
    emb1 = create_embedding(normalized_resume)
    emb2 = create_embedding(normalized_jd)
    
    # Calculate cosine similarity
    similarity = cosine_similarity([emb1], [emb2])[0][0]
    
    return float(round(similarity * 100, 2))