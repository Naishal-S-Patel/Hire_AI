"""
Email service — SMTP-based email sending with retry logic.
Handles all system emails: confirmations, assessments, offers, etc.
"""

import asyncio
import logging
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.application import MIMEApplication
from typing import Optional, List
from pathlib import Path

from app.config import settings

logger = logging.getLogger(__name__)


class EmailService:
    """SMTP email service with retry logic."""
    
    def __init__(
        self,
        smtp_server: str = "smtp.gmail.com",
        smtp_port: int = 587,
        sender_email: str = "",
        sender_password: str = "",
        max_retries: int = 3,
    ):
        self.smtp_server = smtp_server
        self.smtp_port = smtp_port
        self.sender_email = sender_email or settings.EMAIL_ADDRESS
        self.sender_password = sender_password or settings.EMAIL_PASSWORD
        self.max_retries = max_retries
    
    async def send_email(
        self,
        to_email: str,
        subject: str,
        body_html: str,
        body_text: Optional[str] = None,
        attachments: Optional[List[dict]] = None,
    ) -> bool:
        """
        Send email with retry logic.
        
        Args:
            to_email: Recipient email address
            subject: Email subject
            body_html: HTML email body
            body_text: Plain text fallback (optional)
            attachments: List of dicts with 'filename' and 'content' (bytes)
        
        Returns:
            True if sent successfully, False otherwise
        """
        for attempt in range(self.max_retries):
            try:
                # Create message
                msg = MIMEMultipart('alternative')
                msg['From'] = self.sender_email
                msg['To'] = to_email
                msg['Subject'] = subject
                
                # Add text and HTML parts
                if body_text:
                    msg.attach(MIMEText(body_text, 'plain'))
                msg.attach(MIMEText(body_html, 'html'))
                
                # Add attachments
                if attachments:
                    for attachment in attachments:
                        part = MIMEApplication(attachment['content'], Name=attachment['filename'])
                        part['Content-Disposition'] = f'attachment; filename="{attachment["filename"]}"'
                        msg.attach(part)
                
                # Send via SMTP
                await asyncio.to_thread(self._send_smtp, msg)
                
                logger.info(f"Email sent successfully to {to_email}: {subject}")
                return True
                
            except Exception as e:
                logger.error(f"Email send attempt {attempt + 1} failed to {to_email}: {e}")
                if attempt < self.max_retries - 1:
                    await asyncio.sleep(2 ** attempt)  # Exponential backoff
                else:
                    logger.error(f"Failed to send email to {to_email} after {self.max_retries} attempts")
                    return False
        
        return False
    
    def _send_smtp(self, msg: MIMEMultipart):
        """Synchronous SMTP send (called via asyncio.to_thread)."""
        with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
            server.starttls()
            server.login(self.sender_email, self.sender_password)
            server.send_message(msg)
    
    # ── Email Templates ──────────────────────────────────────
    
    async def send_application_confirmation(
        self,
        candidate_email: str,
        candidate_name: str,
        job_title: str,
    ) -> bool:
        """Send application confirmation email."""
        subject = f"Application Received - {job_title}"
        
        html = f"""
        <html>
        <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
            <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
                <h2 style="color: #2563eb;">Application Received</h2>
                <p>Dear {candidate_name},</p>
                <p>Thank you for applying for the <strong>{job_title}</strong> position.</p>
                <p>We have received your application and our team will review it shortly. You will be notified about the next steps via email.</p>
                <p>Best regards,<br>Recruitment Team</p>
                <hr style="border: none; border-top: 1px solid #e5e7eb; margin: 20px 0;">
                <p style="font-size: 12px; color: #6b7280;">This is an automated message. Please do not reply to this email.</p>
            </div>
        </body>
        </html>
        """
        
        text = f"Dear {candidate_name},\n\nThank you for applying for the {job_title} position. We have received your application and will review it shortly.\n\nBest regards,\nRecruitment Team"
        
        return await self.send_email(candidate_email, subject, html, text)
    
    async def send_assessment_invitation(
        self,
        candidate_email: str,
        candidate_name: str,
        job_title: str,
        assessment_link: str,
    ) -> bool:
        """Send technical assessment invitation."""
        subject = f"Technical Assessment - {job_title}"
        
        html = f"""
        <html>
        <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
            <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
                <h2 style="color: #2563eb;">Technical Assessment Invitation</h2>
                <p>Dear {candidate_name},</p>
                <p>Congratulations! Your application for <strong>{job_title}</strong> has been shortlisted.</p>
                <p>Please complete the technical assessment using the link below:</p>
                <p style="text-align: center; margin: 30px 0;">
                    <a href="{assessment_link}" style="background-color: #2563eb; color: white; padding: 12px 24px; text-decoration: none; border-radius: 6px; display: inline-block;">Start Assessment</a>
                </p>
                <p>Please complete the assessment within 48 hours.</p>
                <p>Best regards,<br>Recruitment Team</p>
                <hr style="border: none; border-top: 1px solid #e5e7eb; margin: 20px 0;">
                <p style="font-size: 12px; color: #6b7280;">This is an automated message. Please do not reply to this email.</p>
            </div>
        </body>
        </html>
        """
        
        text = f"Dear {candidate_name},\n\nCongratulations! Your application for {job_title} has been shortlisted.\n\nPlease complete the technical assessment: {assessment_link}\n\nBest regards,\nRecruitment Team"
        
        return await self.send_email(candidate_email, subject, html, text)
    
    async def send_shortlist_notification(
        self,
        candidate_email: str,
        candidate_name: str,
        job_title: str,
    ) -> bool:
        """Send shortlist notification."""
        subject = f"Application Shortlisted - {job_title}"
        
        html = f"""
        <html>
        <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
            <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
                <h2 style="color: #16a34a;">You've Been Shortlisted!</h2>
                <p>Dear {candidate_name},</p>
                <p>Great news! Your application for <strong>{job_title}</strong> has been shortlisted.</p>
                <p>Our HR team will contact you soon with the next steps in the interview process.</p>
                <p>Best regards,<br>Recruitment Team</p>
                <hr style="border: none; border-top: 1px solid #e5e7eb; margin: 20px 0;">
                <p style="font-size: 12px; color: #6b7280;">This is an automated message. Please do not reply to this email.</p>
            </div>
        </body>
        </html>
        """
        
        text = f"Dear {candidate_name},\n\nGreat news! Your application for {job_title} has been shortlisted. Our HR team will contact you soon.\n\nBest regards,\nRecruitment Team"
        
        return await self.send_email(candidate_email, subject, html, text)
    
    async def send_offer_letter(
        self,
        candidate_email: str,
        candidate_name: str,
        job_title: str,
        offer_letter_pdf: Optional[bytes] = None,
    ) -> bool:
        """Send offer letter email with PDF attachment."""
        subject = f"Job Offer - {job_title}"
        
        html = f"""
        <html>
        <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
            <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
                <h2 style="color: #16a34a;">Congratulations! Job Offer</h2>
                <p>Dear {candidate_name},</p>
                <p>We are pleased to offer you the position of <strong>{job_title}</strong>.</p>
                <p>Please find the detailed offer letter attached to this email.</p>
                <p>We look forward to welcoming you to our team!</p>
                <p>Best regards,<br>HR Team</p>
                <hr style="border: none; border-top: 1px solid #e5e7eb; margin: 20px 0;">
                <p style="font-size: 12px; color: #6b7280;">This is an automated message. Please do not reply to this email.</p>
            </div>
        </body>
        </html>
        """
        
        text = f"Dear {candidate_name},\n\nWe are pleased to offer you the position of {job_title}. Please find the offer letter attached.\n\nBest regards,\nHR Team"
        
        attachments = []
        if offer_letter_pdf:
            attachments.append({
                'filename': f'Offer_Letter_{candidate_name.replace(" ", "_")}.pdf',
                'content': offer_letter_pdf
            })
        
        return await self.send_email(candidate_email, subject, html, text, attachments)
    
    async def send_rejection_email(
        self,
        candidate_email: str,
        candidate_name: str,
        job_title: str,
    ) -> bool:
        """Send rejection email."""
        subject = f"Application Update - {job_title}"
        
        html = f"""
        <html>
        <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
            <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
                <h2 style="color: #2563eb;">Application Update</h2>
                <p>Dear {candidate_name},</p>
                <p>Thank you for your interest in the <strong>{job_title}</strong> position.</p>
                <p>After careful consideration, we have decided to move forward with other candidates whose qualifications more closely match our current needs.</p>
                <p>We appreciate the time you invested in the application process and encourage you to apply for future opportunities.</p>
                <p>Best regards,<br>Recruitment Team</p>
                <hr style="border: none; border-top: 1px solid #e5e7eb; margin: 20px 0;">
                <p style="font-size: 12px; color: #6b7280;">This is an automated message. Please do not reply to this email.</p>
            </div>
        </body>
        </html>
        """
        
        text = f"Dear {candidate_name},\n\nThank you for your interest in the {job_title} position. After careful consideration, we have decided to move forward with other candidates.\n\nBest regards,\nRecruitment Team"
        
        return await self.send_email(candidate_email, subject, html, text)


# Global instance
_email_service: Optional[EmailService] = None


def get_email_service() -> EmailService:
    """Get or create the global email service instance."""
    global _email_service
    if _email_service is None:
        _email_service = EmailService()
    return _email_service
