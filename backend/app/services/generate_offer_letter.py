"""
Generate offer letter PDF dynamically.
"""

from datetime import datetime
from io import BytesIO


def generate_offer_letter_pdf(
    candidate_name: str,
    position: str = "Software Engineer",
    department: str = "Engineering",
    salary: str = "As per company standards",
    start_date: str = "",
) -> bytes:
    """
    Generate offer letter PDF using reportlab.
    Falls back to text-based PDF if reportlab is not available.
    """
    try:
        from reportlab.lib.pagesizes import letter
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        from reportlab.lib.units import inch
        from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
        from reportlab.lib.enums import TA_CENTER, TA_LEFT
        from reportlab.lib import colors

        buffer = BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=letter, topMargin=0.75*inch, bottomMargin=0.75*inch)

        styles = getSampleStyleSheet()
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=20,
            textColor=colors.HexColor('#0f766e'),
            spaceAfter=20,
            alignment=TA_CENTER,
            fontName='Helvetica-Bold',
        )

        heading_style = ParagraphStyle(
            'CustomHeading',
            parent=styles['Heading2'],
            fontSize=14,
            textColor=colors.HexColor('#111827'),
            spaceAfter=12,
            fontName='Helvetica-Bold',
        )

        body_style = ParagraphStyle(
            'CustomBody',
            parent=styles['BodyText'],
            fontSize=11,
            textColor=colors.HexColor('#374151'),
            spaceAfter=12,
            alignment=TA_LEFT,
        )

        story = []

        # Header
        story.append(Paragraph("<b>HireAI</b>", title_style))
        story.append(Paragraph("AI-Powered Recruitment Platform", ParagraphStyle(
            'Subtitle',
            parent=body_style,
            fontSize=10,
            textColor=colors.HexColor('#6b7280'),
            alignment=TA_CENTER,
        )))
        story.append(Spacer(1, 0.3*inch))

        # Date
        today = datetime.now().strftime("%B %d, %Y")
        story.append(Paragraph(f"<b>Date:</b> {today}", body_style))
        story.append(Spacer(1, 0.2*inch))

        # Greeting
        story.append(Paragraph(f"Dear <b>{candidate_name}</b>,", body_style))
        story.append(Spacer(1, 0.2*inch))

        # Offer
        story.append(Paragraph("<b>Job Offer Letter</b>", heading_style))
        story.append(Paragraph(
            f"We are pleased to offer you the position of <b>{position}</b> in the <b>{department}</b> department at HireAI.",
            body_style
        ))
        story.append(Spacer(1, 0.2*inch))

        # Position Details Table
        story.append(Paragraph("<b>Position Details:</b>", heading_style))
        
        if not start_date:
            start_date = "To be mutually agreed upon"
        
        details_data = [
            ['Position:', position],
            ['Department:', department],
            ['Compensation:', salary],
            ['Start Date:', start_date],
        ]
        
        details_table = Table(details_data, colWidths=[2*inch, 4*inch])
        details_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (0, -1), colors.HexColor('#f0f9ff')),
            ('TEXTCOLOR', (0, 0), (-1, -1), colors.HexColor('#111827')),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 11),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
            ('TOPPADDING', (0, 0), (-1, -1), 8),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#e5e7eb')),
        ]))
        story.append(details_table)
        story.append(Spacer(1, 0.3*inch))

        # Terms
        story.append(Paragraph("<b>Terms and Conditions:</b>", heading_style))
        story.append(Paragraph(
            "This offer is contingent upon successful completion of background verification and reference checks. "
            "Your employment will be subject to the company's standard terms and conditions.",
            body_style
        ))
        story.append(Spacer(1, 0.2*inch))

        # Acceptance
        story.append(Paragraph(
            "Please confirm your acceptance of this offer by signing and returning this letter within <b>7 business days</b>.",
            body_style
        ))
        story.append(Spacer(1, 0.3*inch))

        # Closing
        story.append(Paragraph(
            "We are excited about the possibility of you joining our team and look forward to your positive response!",
            body_style
        ))
        story.append(Spacer(1, 0.4*inch))

        story.append(Paragraph("Sincerely,", body_style))
        story.append(Spacer(1, 0.5*inch))

        story.append(Paragraph("<b>HR Department</b>", body_style))
        story.append(Paragraph("HireAI", body_style))
        story.append(Paragraph("recruiting@example.com", ParagraphStyle(
            'Email',
            parent=body_style,
            fontSize=10,
            textColor=colors.HexColor('#2563eb'),
        )))

        # Build PDF
        doc.build(story)

        pdf_bytes = buffer.getvalue()
        buffer.close()

        return pdf_bytes

    except ImportError:
        # Fallback: Generate simple text-based PDF
        return _generate_simple_offer_letter(candidate_name, position, department, salary, start_date)


def _generate_simple_offer_letter(
    candidate_name: str,
    position: str,
    department: str,
    salary: str,
    start_date: str,
) -> bytes:
    """Fallback: Generate simple text-based offer letter."""
    today = datetime.now().strftime("%B %d, %Y")
    
    if not start_date:
        start_date = "To be mutually agreed upon"
    
    content = f"""
HireAI
AI-Powered Recruitment Platform

Job Offer Letter

Date: {today}

Dear {candidate_name},

We are pleased to offer you the position of {position} in the {department} department at HireAI.

Position Details:
- Position: {position}
- Department: {department}
- Compensation: {salary}
- Start Date: {start_date}

Terms and Conditions:
This offer is contingent upon successful completion of background verification and reference checks.
Your employment will be subject to the company's standard terms and conditions.

Please confirm your acceptance of this offer by signing and returning this letter within 7 business days.

We are excited about the possibility of you joining our team and look forward to your positive response!

Sincerely,

HR Department
HireAI
recruiting@example.com
"""
    
    return content.encode('utf-8')
