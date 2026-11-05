import os
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT


def build_resume_pdf(data: dict, output_path: str, template: str = "classic-ats") -> str:
    """
    Renders an ATS-optimized, high-fidelity PDF resume based on selected template:
    - 'classic-ats': Standard single-column, dark text, clean dividers.
    - 'modern-tech': Deep navy and indigo accents, modern section bars.
    - 'minimalist-executive': Refined slate tones, elegant hierarchy.
    """
    doc = SimpleDocTemplate(
        output_path,
        pagesize=letter,
        rightMargin=36,
        leftMargin=36,
        topMargin=36,
        bottomMargin=36
    )

    styles = getSampleStyleSheet()

    # Determine colors based on template
    if template == "modern-tech":
        primary_color = colors.HexColor('#312E81')  # Indigo
        accent_color = colors.HexColor('#4F46E5')
        body_color = colors.HexColor('#1E293B')
        name_font = 'Helvetica-Bold'
        heading_font = 'Helvetica-Bold'
        divider_color = colors.HexColor('#6366F1')
    elif template == "minimalist-executive":
        primary_color = colors.HexColor('#0F172A')  # Slate 900
        accent_color = colors.HexColor('#334155')
        body_color = colors.HexColor('#1E293B')
        name_font = 'Helvetica-Bold'
        heading_font = 'Helvetica-Bold'
        divider_color = colors.HexColor('#94A3B8')
    else:  # classic-ats
        primary_color = colors.HexColor('#111827')
        accent_color = colors.HexColor('#1F2937')
        body_color = colors.HexColor('#111827')
        name_font = 'Helvetica-Bold'
        heading_font = 'Helvetica-Bold'
        divider_color = colors.HexColor('#111827')

    name_style = ParagraphStyle(
        'ResName',
        parent=styles['Heading1'],
        fontName=name_font,
        fontSize=20,
        leading=24,
        textColor=primary_color,
        alignment=TA_CENTER if template != 'modern-tech' else TA_LEFT,
        spaceAfter=4
    )

    contact_style = ParagraphStyle(
        'ResContact',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=9,
        leading=12,
        textColor=colors.HexColor('#475569'),
        alignment=TA_CENTER if template != 'modern-tech' else TA_LEFT,
        spaceAfter=12
    )

    section_heading_style = ParagraphStyle(
        'ResSecHeading',
        parent=styles['Heading2'],
        fontName=heading_font,
        fontSize=12,
        leading=15,
        textColor=primary_color,
        spaceBefore=10,
        spaceAfter=4
    )

    item_title_style = ParagraphStyle(
        'ResItemTitle',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=10,
        leading=13,
        textColor=body_color
    )

    item_sub_style = ParagraphStyle(
        'ResItemSub',
        parent=styles['Normal'],
        fontName='Helvetica-Oblique',
        fontSize=9,
        leading=12,
        textColor=colors.HexColor('#475569')
    )

    body_text_style = ParagraphStyle(
        'ResBodyText',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=9.5,
        leading=13.5,
        textColor=body_color,
        spaceAfter=4
    )

    bullet_style = ParagraphStyle(
        'ResBullet',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=9,
        leading=13,
        textColor=body_color,
        leftIndent=12,
        spaceAfter=2
    )

    story = []

    # 1. Header / Personal Info
    full_name = data.get('full_name', 'Your Name').strip()
    story.append(Paragraph(full_name, name_style))

    contact_bits = []
    if data.get('email'):
        contact_bits.append(data['email'])
    if data.get('phone'):
        contact_bits.append(data['phone'])
    if data.get('location'):
        contact_bits.append(data['location'])
    if data.get('linkedin'):
        contact_bits.append(data['linkedin'])
    if data.get('github'):
        contact_bits.append(data['github'])
    if data.get('portfolio'):
        contact_bits.append(data['portfolio'])

    story.append(Paragraph(" | ".join(contact_bits), contact_style))

    # Helper function for section headings
    def add_section_header(title):
        story.append(Paragraph(title.upper(), section_heading_style))
        story.append(HRFlowable(width="100%", thickness=1.0, color=divider_color, spaceAfter=6, spaceBefore=2))

    # 2. Professional Summary
    summary = data.get('summary', '').strip()
    if summary:
        add_section_header("Professional Summary")
        story.append(Paragraph(summary, body_text_style))
        story.append(Spacer(1, 4))

    # 3. Technical Skills
    skills = data.get('skills', '').strip()
    if skills:
        add_section_header("Technical Skills")
        story.append(Paragraph(skills, body_text_style))
        story.append(Spacer(1, 4))

    # 4. Work Experience
    experiences = data.get('experiences', [])
    if experiences:
        add_section_header("Work Experience")
        for exp in experiences:
            role = exp.get('role', '').strip()
            company = exp.get('company', '').strip()
            duration = exp.get('duration', '').strip()
            location = exp.get('location', '').strip()

            title_table_data = [
                [Paragraph(f"<b>{role}</b> — {company}", item_title_style),
                 Paragraph(f"{duration}{(' | ' + location) if location else ''}", item_sub_style)]
            ]
            t = Table(title_table_data, colWidths=[380, 160])
            t.setStyle(TableStyle([
                ('ALIGN', (1, 0), (1, 0), 'RIGHT'),
                ('VALIGN', (0, 0), (-1, -1), 'TOP'),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 2),
                ('TOPPADDING', (0, 0), (-1, -1), 0),
            ]))
            story.append(t)

            desc = exp.get('description', '').strip()
            if desc:
                for line in desc.split('\n'):
                    clean_line = line.strip().lstrip('•-* ')
                    if clean_line:
                        story.append(Paragraph(f"• {clean_line}", bullet_style))
            story.append(Spacer(1, 4))

    # 5. Projects
    projects = data.get('projects', [])
    if projects:
        add_section_header("Projects")
        for proj in projects:
            title = proj.get('title', '').strip()
            tech = proj.get('technologies', '').strip()
            link = proj.get('link', '').strip()

            proj_title_str = f"<b>{title}</b>"
            if tech:
                proj_title_str += f" | <i>{tech}</i>"

            proj_table_data = [
                [Paragraph(proj_title_str, item_title_style),
                 Paragraph(link if link else "", item_sub_style)]
            ]
            t = Table(proj_table_data, colWidths=[400, 140])
            t.setStyle(TableStyle([
                ('ALIGN', (1, 0), (1, 0), 'RIGHT'),
                ('VALIGN', (0, 0), (-1, -1), 'TOP'),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 2),
                ('TOPPADDING', (0, 0), (-1, -1), 0),
            ]))
            story.append(t)

            desc = proj.get('description', '').strip()
            if desc:
                for line in desc.split('\n'):
                    clean_line = line.strip().lstrip('•-* ')
                    if clean_line:
                        story.append(Paragraph(f"• {clean_line}", bullet_style))
            story.append(Spacer(1, 4))

    # 6. Education
    education_list = data.get('education', [])
    if education_list:
        add_section_header("Education")
        for edu in education_list:
            degree = edu.get('degree', '').strip()
            institution = edu.get('institution', '').strip()
            year = edu.get('year', '').strip()
            score = edu.get('score', '').strip()

            edu_table_data = [
                [Paragraph(f"<b>{degree}</b> — {institution}", item_title_style),
                 Paragraph(f"{year}{(' | GPA: ' + score) if score else ''}", item_sub_style)]
            ]
            t = Table(edu_table_data, colWidths=[400, 140])
            t.setStyle(TableStyle([
                ('ALIGN', (1, 0), (1, 0), 'RIGHT'),
                ('VALIGN', (0, 0), (-1, -1), 'TOP'),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 2),
                ('TOPPADDING', (0, 0), (-1, -1), 0),
            ]))
            story.append(t)
            story.append(Spacer(1, 2))

    # 7. Certifications
    certifications = data.get('certifications', '').strip()
    if certifications:
        add_section_header("Certifications & Licenses")
        for cert in certifications.split('\n'):
            clean_cert = cert.strip().lstrip('•-* ')
            if clean_cert:
                story.append(Paragraph(f"• {clean_cert}", bullet_style))

    doc.build(story)
    return output_path
