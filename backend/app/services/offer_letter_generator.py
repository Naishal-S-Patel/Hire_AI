"""
Offer letter PDF generator.
"""

from datetime import datetime
from io import BytesIO
from typing import Optional

try:
    from reportlab.lib.pagesizes import letter
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import inch
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
    from reportlab.lib.enums import TA_CENTER, TA_LEFT
    REPORTLAB_AVAILABLE = True
except ImportError:
    REPORTLAB_AVAILABLE = False


def generate_offer_letter_pdf(
    candidate_name: str,
    job_title: str,
    salary: Optional[str] = None,
    start_date: Optional[str] = None,
    company_name: str = "TalentHire Inc.",
) -> bytes:
    """
    Generate offer letter PDF.
    
    Args:
        candidate_name: Full name of candidate
        job_title: Position title
        salary: Salary information (optional)
        start_date: Expected start date (optional)
        company_name: Company name
    
    Returns:
        PDF file as bytes
    """
    if not REPORTLAB_AVAILABLE:
        # Fallback: return simple text-based PDF placeholder
        return _generate_simple_offer_letter(candidate_name, job_title, salary, start_date, company_name)
    
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter, topMargin=0.75*inch, bottomMargin=0.75*inch)
    
    # Styles
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=18,
        textColor='#2563eb',
        spaceAfter=30,
        alignment=TA_CENTER,
    )
    
    heading_style = ParagraphStyle(
        'CustomHeading',
        parent=styles['Heading2'],
        fontSize=14,
        textColor='#111827',
        spaceAfter=12,
    )
    
    body_style = ParagraphStyle(
        'CustomBody',
        parent=styles['BodyText'],
        fontSize=11,
        textColor='#374151',
        spaceAfter=12,
        alignment=TA_LEFT,
    )
    
    # Build content
    story = []
    
    # Header
    story.append(Paragraph(f"<b>{company_name}</b>", title_style))
    story.append(Spacer(1, 0.2*inch))
    
    # Date
    today = datetime.now().strftime("%B %d, %Y")
    story.append(Paragraph(today, body_style))
    story.append(Spacer(1, 0.3*inch))
    
    # Greeting
    story.append(Paragraph(f"Dear {candidate_name},", body_style))
    story.append(Spacer(1, 0.2*inch))
    
    # Offer
    story.append(Paragraph("<b>Job Offer</b>", heading_style))
    story.append(Paragraph(
        f"We are pleased to offer you the position of <b>{job_title}</b> at {company_name}.",
        body_style
    ))
    story.append(Spacer(1, 0.2*inch))
    
    # Details
    if salary or start_date:
        story.append(Paragraph("<b>Position Details:</b>", heading_style))
        
        if salary:
            story.append(Paragraph(f"• <b>Compensation:</b> {salary}", body_style))
        
        if start_date:
            story.append(Paragraph(f"• <b>Start Date:</b> {start_date}", body_style))
        else:
            story.append(Paragraph("• <b>Start Date:</b> To be mutually agreed upon", body_style))
        
        story.append(Spacer(1, 0.2*inch))
    
    # Terms
    story.append(Paragraph(
        "This offer is contingent upon successful completion of background verification and reference checks.",
        body_style
    ))
    story.append(Spacer(1, 0.2*inch))
    
    # Acceptance
    story.append(Paragraph(
        "Please confirm your acceptance of this offer by signing and returning this letter within 7 days.",
        body_style
    ))
    story.append(Spacer(1, 0.3*inch))
    
    # Closing
    story.append(Paragraph("We look forward to welcoming you to our team!", body_style))
    story.append(Spacer(1, 0.3*inch))
    
    story.append(Paragraph("Sincerely,", body_style))
    story.append(Spacer(1, 0.5*inch))
    
    story.append(Paragraph("<b>HR Department</b>", body_style))
    story.append(Paragraph(company_name, body_style))
    
    # Build PDF
    doc.build(story)
    
    pdf_bytes = buffer.getvalue()
    buffer.close()
    
    return pdf_bytes


def _generate_simple_offer_letter(
    candidate_name: str,
    job_title: str,
    salary: Optional[str],
    start_date: Optional[str],
    company_name: str,
) -> bytes:
    """Fallback: Generate simple text-based offer letter."""
    today = datetime.now().strftime("%B %d, %Y")
    
    content = f"""
{company_name}
Job Offer Letter

Date: {today}

Dear {candidate_name},

We are pleased to offer you the position of {job_title} at {company_name}.

Position Details:
"""
    
    if salary:
        content += f"- Compensation: {salary}\n"
    
    if start_date:
        content += f"- Start Date: {start_date}\n"
    else:
        content += "- Start Date: To be mutually agreed upon\n"
    
    content += """
This offer is contingent upon successful completion of background verification and reference checks.

Please confirm your acceptance of this offer by signing and returning this letter within 7 days.

We look forward to welcoming you to our team!

Sincerely,

HR Department
""" + company_name
    
    return content.encode('utf-8')
