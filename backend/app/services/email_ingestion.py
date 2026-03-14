"""
Email ingestion service — automatically fetch resumes from email inbox.
Runs as a background task checking every 60 seconds.
"""

import asyncio
import hashlib
import imaplib
import email
import os
from email.header import decode_header
from typing import List, Optional

import aiofiles
import httpx
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.db import async_session as async_session_maker
from app.models.application import Application
from app.models.candidate import Candidate
from app.models.job import Job


class EmailIngestionService:
    """Background service to ingest resumes from email."""
    
    def __init__(
        self,
        imap_server: str,
        email_address: str,
        password: str,
        check_interval: int = 60,
    ):
        self.imap_server = imap_server
        self.email_address = email_address
        self.password = password
        self.check_interval = check_interval
        self.running = False
    
    async def start(self):
        """Start the background ingestion loop."""
        self.running = True
        while self.running:
            try:
                await self.check_inbox()
            except Exception as e:
                print(f"Email ingestion error: {e}")
            await asyncio.sleep(self.check_interval)
    
    def stop(self):
        """Stop the background loop."""
        self.running = False
    
    async def check_inbox(self):
        """Check inbox for new resumes."""
        # Connect to IMAP server
        mail = imaplib.IMAP4_SSL(self.imap_server)
        mail.login(self.email_address, self.password)
        mail.select("inbox")
        
        # Search for unread emails
        status, messages = mail.search(None, "UNSEEN")
        if status != "OK":
            return
        
        email_ids = messages[0].split()
        
        for email_id in email_ids:
            try:
                await self.process_email(mail, email_id)
            except Exception as e:
                print(f"Error processing email {email_id}: {e}")
        
        mail.close()
        mail.logout()
    
    async def process_email(self, mail, email_id):
        """Process a single email and extract resume."""
        status, msg_data = mail.fetch(email_id, "(RFC822)")
        if status != "OK":
            return
        
        # Parse email
        raw_email = msg_data[0][1]
        msg = email.message_from_bytes(raw_email)
        
        # Extract sender info
        from_header = msg.get("From", "")
        sender_email = email.utils.parseaddr(from_header)[1]
        sender_name = email.utils.parseaddr(from_header)[0] or "Unknown"
        
        # Extract attachments
        attachments = []
        for part in msg.walk():
            if part.get_content_maintype() == "multipart":
                continue
            if part.get("Content-Disposition") is None:
                continue
            
            filename = part.get_filename()
            if filename:
                # Decode filename if needed
                decoded = decode_header(filename)
                filename = decoded[0][0]
                if isinstance(filename, bytes):
                    filename = filename.decode()
                
                # Check if it's a resume file
                if filename.lower().endswith((".pdf", ".docx", ".doc")):
                    attachments.append({
                        "filename": filename,
                        "data": part.get_payload(decode=True)
                    })
        
        # Process each resume attachment
        for attachment in attachments:
            await self.ingest_resume(
                sender_name=sender_name,
                sender_email=sender_email,
                filename=attachment["filename"],
                file_data=attachment["data"],
            )
    
    async def ingest_resume(
        self,
        sender_name: str,
        sender_email: str,
        filename: str,
        file_data: bytes,
    ):
        """Ingest a resume from email."""
        async with async_session_maker() as db:
            # Save file
            os.makedirs(settings.UPLOADS_DIR, exist_ok=True)
            file_path = os.path.join(settings.UPLOADS_DIR, f"email_{sender_email}_{filename}")
            
            async with aiofiles.open(file_path, "wb") as f:
                await f.write(file_data)
            
            # Calculate hash
            resume_hash = hashlib.sha256(file_data).hexdigest()
            
            # Check for duplicate
            result = await db.execute(
                select(Candidate).where(Candidate.resume_hash == resume_hash)
            )
            if result.scalar_one_or_none():
                print(f"Duplicate resume from {sender_email}, skipping")
                return
            
            # Parse resume via ML service
            try:
                parsed_data = await self.parse_resume_via_ml(file_path)
            except Exception as e:
                print(f"Resume parsing failed for {sender_email}: {e}")
                return
            
            # Extract data
            skills = parsed_data.get("skills", [])
            if isinstance(skills, str):
                skills = [s.strip() for s in skills.split() if s.strip()]
            
            experience_years = float(parsed_data.get("experience_years", 0))
            resume_text = parsed_data.get("resume_text", "")
            education = parsed_data.get("education", [])
            
            # Generate AI summary
            ai_summary = await self.generate_ai_summary(resume_text, skills, experience_years)
            
            # Calculate risk score
            risk_score = self.calculate_risk_score(skills, experience_years)
            
            # Create or update candidate
            result = await db.execute(select(Candidate).where(Candidate.email == sender_email))
            candidate = result.scalar_one_or_none()
            
            if not candidate:
                candidate = Candidate(
                    full_name=sender_name,
                    email=sender_email,
                    skills=skills,
                    experience_years=experience_years,
                    education=education,
                    resume_path=filename,
                    resume_file_url=file_path,
                    resume_text=resume_text,
                    resume_hash=resume_hash,
                    ai_summary=ai_summary,
                    source="EMAIL",
                    parsed_json=parsed_data,
                )
                db.add(candidate)
                await db.flush()
            
            # Find most recent active job (or create application without specific job)
            result = await db.execute(
                select(Job)
                .where(Job.is_active == True)
                .order_by(Job.created_at.desc())
                .limit(1)
            )
            job = result.scalar_one_or_none()
            
            if job:
                # Calculate ATS score
                ats_score = self.calculate_ats_score(skills, experience_years, job)
                
                # Create application
                application = Application(
                    job_id=job.id,
                    candidate_id=candidate.id,
                    candidate_name=sender_name,
                    candidate_email=sender_email,
                    resume_file_url=file_path,
                    resume_text=resume_text,
                    experience_years=experience_years,
                    skills=skills,
                    education=education,
                    ai_summary=ai_summary,
                    ats_score=ats_score,
                    risk_score=risk_score,
                    status="PENDING",
                    source="EMAIL",
                )
                
                db.add(application)
                await db.commit()
                
                print(f"Ingested resume from {sender_email} for job {job.title}")
    
    async def parse_resume_via_ml(self, file_path: str) -> dict:
        """Call ML service to parse resume."""
        async with httpx.AsyncClient(timeout=60.0) as client:
            with open(file_path, "rb") as f:
                files = {"file": (os.path.basename(file_path), f, "application/pdf")}
                response = await client.post(
                    f"{settings.ML_SERVICE_URL}/parse_resume",
                    files=files
                )
                response.raise_for_status()
                return response.json()
    
    async def generate_ai_summary(self, resume_text: str, skills: List[str], experience: float) -> str:
        """Generate AI summary using OpenAI."""
        if not settings.OPENAI_API_KEY:
            return f"Professional with {experience} years of experience in {', '.join(skills[:5])}."
        
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    "https://api.openai.com/v1/chat/completions",
                    headers={
                        "Authorization": f"Bearer {settings.OPENAI_API_KEY}",
                        "Content-Type": "application/json",
                    },
                    json={
                        "model": "gpt-3.5-turbo",
                        "messages": [
                            {
                                "role": "system",
                                "content": "You are a recruiter assistant. Generate concise 2-3 sentence candidate summaries."
                            },
                            {
                                "role": "user",
                                "content": f"Generate a professional summary for a candidate with {experience} years of experience. Key skills: {', '.join(skills[:10])}. Resume excerpt: {resume_text[:500]}"
                            }
                        ],
                        "max_tokens": 150,
                        "temperature": 0.7,
                    }
                )
                response.raise_for_status()
                data = response.json()
                return data["choices"][0]["message"]["content"].strip()
        except Exception as e:
            print(f"OpenAI API error: {e}")
            return f"Professional with {experience} years of experience in {', '.join(skills[:5])}."
    
    def calculate_ats_score(self, candidate_skills: List[str], candidate_exp: float, job: Job) -> float:
        """Calculate ATS score."""
        skill_match_weight = 0.5
        experience_weight = 0.3
        education_weight = 0.2
        
        required_skills = set(s.lower() for s in (job.required_skills or []))
        candidate_skills_lower = set(s.lower() for s in candidate_skills)
        
        if required_skills:
            skill_match = len(required_skills & candidate_skills_lower) / len(required_skills)
        else:
            skill_match = 0.5
        
        if job.experience_required and candidate_exp is not None:
            if candidate_exp >= job.experience_required:
                exp_match = 1.0
            else:
                exp_match = candidate_exp / job.experience_required
        else:
            exp_match = 0.5
        
        edu_match = 0.5
        
        score = (
            skill_match * skill_match_weight +
            exp_match * experience_weight +
            edu_match * education_weight
        ) * 100
        
        return min(100, max(0, score))
    
    def calculate_risk_score(self, skills: List[str], experience: float) -> float:
        """Calculate fraud/risk score."""
        risk = 0
        
        if experience == 0 and len(skills) > 15:
            risk += 20
        
        return min(100, risk)


# Global instance (to be started in main.py if configured)
email_service: Optional[EmailIngestionService] = None


def get_email_service() -> Optional[EmailIngestionService]:
    """Get the global email ingestion service instance."""
    return email_service


def init_email_service(
    imap_server: str,
    email_address: str,
    password: str,
) -> EmailIngestionService:
    """Initialize the email ingestion service."""
    global email_service
    email_service = EmailIngestionService(
        imap_server=imap_server,
        email_address=email_address,
        password=password,
    )
    return email_service
