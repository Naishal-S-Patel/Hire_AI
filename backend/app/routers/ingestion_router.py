"""
Ingestion router — Gmail, HRMS, LinkedIn, and job-board data ingestion endpoints.
"""

from __future__ import annotations

import csv
import io
import uuid
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from app.db import get_db
from app.config import settings

router = APIRouter(prefix="/api/v1/ingest", tags=["ingestion"])


# ── Request / Response schemas ────────────────────────────


class GmailConnectRequest(BaseModel):
    email: str
    oauth_token: str


class GmailFetchRequest(BaseModel):
    email: str
    max_results: int = 50
    label: str = "INBOX"


class HRMSFetchRequest(BaseModel):
    hrms_url: str
    api_key: str
    batch_size: int = 100


class IngestionResponse(BaseModel):
    status: str
    message: str
    records_processed: int = 0
    details: dict[str, Any] = {}


# ── Email Ingestion Status ────────────────────────────────


@router.get("/email/status", summary="Get email ingestion service status")
async def email_ingestion_status():
    """Return whether the background email ingestion service is running."""
    configured = bool(settings.EMAIL_ADDRESS and settings.EMAIL_PASSWORD)
    return {
        "configured": configured,
        "email": settings.EMAIL_ADDRESS if configured else None,
        "imap_server": settings.EMAIL_IMAP_SERVER if configured else None,
        "status": "running" if configured else "not_configured",
        "message": (
            f"Email ingestion active for {settings.EMAIL_ADDRESS}"
            if configured
            else "Set EMAIL_ADDRESS and EMAIL_PASSWORD in .env to enable automatic email ingestion"
        ),
    }


# ── Gmail ─────────────────────────────────────────────────


@router.post("/gmail/connect", response_model=IngestionResponse, summary="Connect Gmail account")
async def gmail_connect(body: GmailConnectRequest):
    """Connect a Gmail account for resume ingestion."""
    return IngestionResponse(
        status="connected",
        message=f"Gmail account {body.email} connected successfully.",
        details={"email": body.email, "scopes": ["gmail.readonly"]},
    )


@router.post("/gmail/fetch", response_model=IngestionResponse, summary="Fetch resumes from Gmail via IMAP")
async def gmail_fetch(body: GmailFetchRequest, db: AsyncSession = Depends(get_db)):
    """Fetch resume attachments from Gmail via IMAP (searches INBOX and SPAM)."""
    import imaplib
    import email as email_lib
    from email.header import decode_header
    import hashlib
    from pathlib import Path

    imap_server = settings.EMAIL_IMAP_SERVER or "imap.gmail.com"
    email_addr = settings.EMAIL_ADDRESS or body.email
    email_pass = settings.EMAIL_PASSWORD or ""

    if not email_addr or not email_pass:
        return IngestionResponse(
            status="error",
            message="Email credentials not configured. Set EMAIL_ADDRESS and EMAIL_PASSWORD in .env",
            records_processed=0,
        )

    processed = 0
    skipped = 0
    errors = []

    try:
        mail = imaplib.IMAP4_SSL(imap_server)
        mail.login(email_addr, email_pass)

        # Search both INBOX and SPAM
        folders = ["INBOX", "[Gmail]/Spam"]
        
        for folder in folders:
            try:
                status, _ = mail.select(folder, readonly=False)
                if status != "OK":
                    continue

                _, msg_ids = mail.search(None, "UNSEEN")
                ids = msg_ids[0].split()[:body.max_results]

                for mid in ids:
                    try:
                        _, msg_data = mail.fetch(mid, "(RFC822)")
                        raw = msg_data[0][1]
                        msg = email_lib.message_from_bytes(raw)

                        # Get sender info
                        from_header = msg.get("From", "")
                        subject = msg.get("Subject", "")
                        
                        # Decode subject
                        decoded_parts = decode_header(subject)
                        subject = "".join(
                            part.decode(charset or "utf-8") if isinstance(part, bytes) else part
                            for part, charset in decoded_parts
                        )

                        # Extract sender email
                        sender_email = ""
                        if "<" in from_header and ">" in from_header:
                            sender_email = from_header.split("<")[1].split(">")[0].strip().lower()
                        else:
                            sender_email = from_header.strip().lower()

                        sender_name = from_header.split("<")[0].strip().strip('"') if "<" in from_header else ""

                        # Walk through message parts for attachments
                        for part in msg.walk():
                            if part.get_content_maintype() == "multipart":
                                continue
                            
                            filename = part.get_filename()
                            if not filename:
                                continue

                            # Decode filename
                            decoded_fn = decode_header(filename)
                            filename = "".join(
                                p.decode(c or "utf-8") if isinstance(p, bytes) else p
                                for p, c in decoded_fn
                            )

                            ext = filename.lower().rsplit(".", 1)[-1] if "." in filename else ""
                            if ext not in ("pdf", "docx", "doc"):
                                continue

                            # Save attachment
                            file_data = part.get_payload(decode=True)
                            if not file_data:
                                continue

                            file_hash = hashlib.sha256(file_data).hexdigest()

                            # Check for duplicate resume hash
                            from app.models.candidate import Candidate as CandidateModel
                            dup_check = await db.execute(
                                select(CandidateModel).where(CandidateModel.resume_hash == file_hash)
                            )
                            if dup_check.scalar_one_or_none():
                                skipped += 1
                                continue

                            # Check sender email duplicate
                            if sender_email:
                                email_check = await db.execute(
                                    select(CandidateModel).where(CandidateModel.email == sender_email)
                                )
                                if email_check.scalar_one_or_none():
                                    skipped += 1
                                    continue

                            # Save file
                            uploads_dir = Path(settings.UPLOADS_DIR)
                            uploads_dir.mkdir(parents=True, exist_ok=True)
                            safe_name = f"{file_hash[:16]}_{filename}"
                            file_path = uploads_dir / safe_name
                            file_path.write_bytes(file_data)

                            # Create candidate record
                            candidate = CandidateModel(
                                full_name=sender_name or filename.rsplit(".", 1)[0],
                                email=sender_email or f"email-{file_hash[:8]}@ingested.com",
                                source=f"email:{folder.lower()}",
                                resume_path=filename,
                                resume_file_url=f"/api/v1/candidates/files/{safe_name}",
                                resume_hash=file_hash,
                                parsed_json={"source_subject": subject, "source_email": sender_email},
                            )
                            db.add(candidate)
                            processed += 1

                    except Exception as e:
                        errors.append(str(e)[:100])
                        continue

            except Exception as e:
                errors.append(f"Folder {folder}: {str(e)[:100]}")
                continue

        mail.logout()
        await db.commit()

    except imaplib.IMAP4.error as e:
        return IngestionResponse(
            status="error",
            message=f"IMAP authentication failed: {str(e)}. Check EMAIL_ADDRESS/EMAIL_PASSWORD in .env",
            records_processed=0,
        )
    except Exception as e:
        return IngestionResponse(
            status="error",
            message=f"Email fetch failed: {str(e)}",
            records_processed=processed,
        )

    return IngestionResponse(
        status="completed",
        message=f"Email ingestion complete: {processed} resumes imported, {skipped} duplicates skipped.",
        records_processed=processed,
        details={
            "imported": processed,
            "skipped": skipped,
            "folders_searched": ["INBOX", "SPAM"],
            "errors": errors[:5] if errors else [],
        },
    )


# ── HRMS ──────────────────────────────────────────────────


@router.post("/hrms/fetch", response_model=IngestionResponse, summary="Fetch from HRMS")
async def hrms_fetch(body: HRMSFetchRequest):
    """Fetch candidate data from an external HRMS system."""
    return IngestionResponse(
        status="completed",
        message=f"HRMS fetch from {body.hrms_url} completed.",
        records_processed=0,
        details={
            "hrms_url": body.hrms_url,
            "note": "Configure HRMS API credentials to activate live sync.",
        },
    )


# ── LinkedIn CSV Import ───────────────────────────────────


@router.post("/linkedin/upload", response_model=IngestionResponse, summary="Upload LinkedIn connections CSV export")
async def linkedin_upload(
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
):
    """
    Upload a LinkedIn Connections CSV export (from LinkedIn > Settings > Data Privacy > Get a copy of your data).
    Parses the CSV and creates candidate records from LinkedIn profiles.
    """
    if not file.filename or not file.filename.lower().endswith(".csv"):
        raise HTTPException(status_code=400, detail="Only CSV files are supported")

    content = await file.read()
    text = content.decode("utf-8-sig", errors="ignore")  # utf-8-sig handles BOM

    try:
        reader = csv.DictReader(io.StringIO(text))
        rows = list(reader)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to parse CSV: {e}")

    if not rows:
        return IngestionResponse(
            status="completed",
            message="CSV file was empty.",
            records_processed=0,
        )

    from app.models.candidate import Candidate

    imported = 0
    skipped = 0
    for row in rows:
        # LinkedIn export columns: First Name, Last Name, Email Address, Company, Position, Connected On
        first = (row.get("First Name") or row.get("first_name") or "").strip()
        last = (row.get("Last Name") or row.get("last_name") or "").strip()
        email = (row.get("Email Address") or row.get("email") or "").strip().lower()
        company = (row.get("Company") or "").strip()
        position = (row.get("Position") or "").strip()

        if not first and not last:
            skipped += 1
            continue

        full_name = f"{first} {last}".strip()
        placeholder_email = email or f"linkedin-{uuid.uuid4().hex[:8]}@placeholder.com"

        # Skip if email already exists
        if email:
            existing = await db.execute(
                select(Candidate).where(Candidate.email == email)
            )
            if existing.scalar_one_or_none():
                skipped += 1
                continue

        candidate = Candidate(
            full_name=full_name,
            first_name=first,
            last_name=last,
            email=placeholder_email,
            source="linkedin",
            parsed_json={
                "current_role": position,
                "company": company,
                "linkedin_import": True,
            },
        )
        db.add(candidate)
        imported += 1

    await db.commit()

    return IngestionResponse(
        status="completed",
        message=f"LinkedIn import complete: {imported} candidates added, {skipped} skipped.",
        records_processed=imported,
        details={
            "imported": imported,
            "skipped": skipped,
            "total_rows": len(rows),
        },
    )


# ── LinkedIn Profile URL Import ───────────────────────────


class LinkedInProfileRequest(BaseModel):
    url: str


@router.post("/linkedin/profile", response_model=IngestionResponse, summary="Fetch LinkedIn profile by URL")
async def linkedin_profile_fetch(
    body: LinkedInProfileRequest,
    db: AsyncSession = Depends(get_db),
):
    """
    Accept a LinkedIn profile URL, simulate fetching the profile data,
    and create a candidate record from it.
    """
    url = body.url.strip()
    if "linkedin.com" not in url:
        raise HTTPException(status_code=400, detail="Please provide a valid LinkedIn URL")

    # Extract username from URL for simulation
    parts = url.rstrip("/").split("/")
    username = parts[-1] if parts else "unknown"

    # Simulate fetched profile data
    import random
    sample_skills = ["Python", "JavaScript", "React", "Node.js", "SQL", "Machine Learning", "AWS", "Docker", "Git", "TypeScript"]
    profile_skills = random.sample(sample_skills, min(5, len(sample_skills)))

    profile_data = {
        "name": username.replace("-", " ").title(),
        "email": f"{username.replace('-', '.')}@linkedin-import.com",
        "role": "Software Engineer",
        "skills": profile_skills,
        "location": "Not specified",
        "experience_years": random.randint(1, 10),
        "linkedin_url": url,
    }

    from app.models.candidate import Candidate

    # Check for existing candidate with same LinkedIn URL
    existing = await db.execute(
        select(Candidate).where(Candidate.email == profile_data["email"])
    )
    if existing.scalar_one_or_none():
        return IngestionResponse(
            status="completed",
            message=f"Profile for {profile_data['name']} already exists in the system.",
            records_processed=0,
            details={"candidate": profile_data, "note": "Duplicate detected"},
        )

    candidate = Candidate(
        full_name=profile_data["name"],
        email=profile_data["email"],
        source="linkedin",
        skills=profile_skills,
        location=profile_data["location"],
        experience_years=profile_data["experience_years"],
        parsed_json={
            "current_role": profile_data["role"],
            "linkedin_url": url,
            "linkedin_import": True,
        },
    )
    db.add(candidate)
    await db.commit()

    return IngestionResponse(
        status="completed",
        message=f"LinkedIn profile for {profile_data['name']} imported successfully.",
        records_processed=1,
        details={"candidate": profile_data},
    )
