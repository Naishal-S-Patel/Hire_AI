"""
Seed script — populates the database with sample data for development.

Usage:
    docker compose exec backend python seed.py
"""

import asyncio
import uuid
from datetime import datetime, timezone

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import async_session, init_db
from app.models.candidate import Candidate
from app.models.job import Job
from app.models.application import Application


SAMPLE_CANDIDATES = [
    {
        "full_name": "Alice Johnson",
        "email": "alice.johnson@example.com",
        "phone": "+1-555-0101",
        "location": "San Francisco, CA",
        "experience_years": 6,
        "skills": ["python", "fastapi", "react", "postgresql", "docker", "aws", "machine learning"],
        "education": [{"degree": "M.S. Computer Science", "institution": "Stanford University"}],
        "source": "seed",
    },
    {
        "full_name": "Bob Smith",
        "email": "bob.smith@example.com",
        "phone": "+1-555-0102",
        "location": "New York, NY",
        "experience_years": 4,
        "skills": ["java", "spring", "kubernetes", "sql", "react", "typescript"],
        "education": [{"degree": "B.S. Software Engineering", "institution": "NYU"}],
        "source": "seed",
    },
    {
        "full_name": "Carol Williams",
        "email": "carol.williams@example.com",
        "phone": "+1-555-0103",
        "location": "Austin, TX",
        "experience_years": 8,
        "skills": ["python", "django", "tensorflow", "pytorch", "deep learning", "nlp", "docker"],
        "education": [
            {"degree": "Ph.D. Artificial Intelligence", "institution": "UT Austin"},
            {"degree": "B.S. Mathematics", "institution": "Rice University"},
        ],
        "source": "seed",
    },
    {
        "full_name": "David Lee",
        "email": "david.lee@example.com",
        "phone": "+1-555-0104",
        "location": "Seattle, WA",
        "experience_years": 3,
        "skills": ["javascript", "react", "node.js", "mongodb", "css", "html", "graphql"],
        "education": [{"degree": "B.S. Computer Science", "institution": "University of Washington"}],
        "source": "seed",
    },
    {
        "full_name": "Eva Martinez",
        "email": "eva.martinez@example.com",
        "phone": "+1-555-0105",
        "location": "Chicago, IL",
        "experience_years": 10,
        "skills": ["python", "aws", "terraform", "kubernetes", "docker", "ci/cd", "linux", "postgresql"],
        "education": [{"degree": "M.S. DevOps Engineering", "institution": "Illinois Tech"}],
        "source": "seed",
    },
]

SAMPLE_JOBS = [
    {
        "title": "Senior Backend Engineer",
        "company": "TechCorp Inc.",
        "description": (
            "We are looking for a senior backend engineer with 5+ years of experience "
            "in Python, FastAPI or Django, PostgreSQL, and cloud infrastructure (AWS/GCP). "
            "Experience with Docker, Kubernetes, and CI/CD pipelines is preferred."
        ),
        "requirements": ["python", "postgresql", "docker", "5+ years experience"],
        "preferred_skills": ["fastapi", "kubernetes", "aws", "terraform"],
        "location": "San Francisco, CA",
        "min_experience": 5,
        "max_experience": 12,
        "salary_range": {"min": 150000, "max": 220000, "currency": "USD"},
    },
    {
        "title": "Machine Learning Engineer",
        "company": "AI Innovations Ltd.",
        "description": (
            "Join our ML team to build production NLP and computer vision pipelines. "
            "Must have experience with PyTorch or TensorFlow, Python, and cloud deployment. "
            "Research publication experience is a plus."
        ),
        "requirements": ["python", "pytorch", "machine learning", "3+ years experience"],
        "preferred_skills": ["nlp", "deep learning", "tensorflow", "docker"],
        "location": "Austin, TX",
        "min_experience": 3,
        "max_experience": 8,
        "salary_range": {"min": 140000, "max": 200000, "currency": "USD"},
    },
    {
        "title": "Full Stack Developer",
        "company": "WebDev Studios",
        "description": (
            "We need a full stack developer proficient in React, Node.js, and databases. "
            "You will build and maintain web applications for our SaaS platform."
        ),
        "requirements": ["react", "node.js", "javascript", "2+ years experience"],
        "preferred_skills": ["typescript", "graphql", "mongodb", "postgresql"],
        "location": "Remote",
        "min_experience": 2,
        "max_experience": 6,
        "salary_range": {"min": 100000, "max": 150000, "currency": "USD"},
    },
]


async def seed():
    """Insert sample data into the database."""
    await init_db()

    async with async_session() as session:
        # Check if data already exists
        result = await session.execute(text("SELECT COUNT(*) FROM candidates"))
        count = result.scalar()
        if count and count > 0:
            print(f"Database already has {count} candidates. Skipping seed.")
            return

        # Insert candidates
        candidate_ids = []
        for data in SAMPLE_CANDIDATES:
            candidate = Candidate(**data)
            session.add(candidate)
            await session.flush()
            candidate_ids.append(candidate.id)
            print(f"  ✓ Created candidate: {data['full_name']}")

        # Insert jobs
        job_ids = []
        for data in SAMPLE_JOBS:
            job = Job(**data)
            session.add(job)
            await session.flush()
            job_ids.append(job.id)
            print(f"  ✓ Created job: {data['title']}")

        # Create sample applications
        if candidate_ids and job_ids:
            applications = [
                Application(candidate_id=candidate_ids[0], job_id=job_ids[0], status="shortlisted"),
                Application(candidate_id=candidate_ids[2], job_id=job_ids[1], status="applied"),
                Application(candidate_id=candidate_ids[3], job_id=job_ids[2], status="interview"),
            ]
            for app in applications:
                session.add(app)
            print(f"  ✓ Created {len(applications)} sample applications")

        await session.commit()
        print(f"\n✅ Seed complete: {len(SAMPLE_CANDIDATES)} candidates, {len(SAMPLE_JOBS)} jobs.")


if __name__ == "__main__":
    asyncio.run(seed())
