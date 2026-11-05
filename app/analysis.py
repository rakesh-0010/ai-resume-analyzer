import os
import re
import json
from datetime import datetime
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from app.resume_parser import parse_resume, ACTION_VERBS
from app.ai_service import AIService


def calculate_ats_scores(parsed_data: dict, raw_text: str) -> dict:
    """
    Transparent, deterministic ATS scoring engine.
    Never produces random numbers.
    
    Weights:
    - Completeness: 25%
    - Skills: 25%
    - Keywords: 20%
    - Content Quality: 15%
    - Formatting: 15%
    """
    # 1. Completeness Score (0-100)
    contact = parsed_data.get('contact', {})
    present_sections = parsed_data.get('present_sections', [])
    
    comp_points = 0
    # Contact points (30 max)
    if contact.get('email'):
        comp_points += 10
    if contact.get('phone'):
        comp_points += 10
    if contact.get('linkedin') or contact.get('github'):
        comp_points += 10
        
    # Core Sections (70 max)
    if 'summary' in present_sections:
        comp_points += 15
    if 'skills' in present_sections:
        comp_points += 15
    if 'experience' in present_sections:
        comp_points += 20
    if 'education' in present_sections:
        comp_points += 10
    if 'projects' in present_sections:
        comp_points += 5
    if 'certifications' in present_sections or 'achievements' in present_sections:
        comp_points += 5
        
    completeness_score = min(100.0, float(comp_points))

    # 2. Skills Score (0-100)
    skills_meta = parsed_data.get('skills', {})
    skill_count = skills_meta.get('total_count', 0)
    cats_represented = len(skills_meta.get('categorized', {}))

    if skill_count == 0:
        skills_score = 15.0
    elif skill_count <= 4:
        skills_score = 45.0 + (skill_count * 5.0)
    elif skill_count <= 8:
        skills_score = 65.0 + ((skill_count - 4) * 3.5)
    elif skill_count <= 14:
        skills_score = 80.0 + ((skill_count - 8) * 2.0)
    else:
        skills_score = 92.0 + min(8.0, (skill_count - 14) * 0.5)

    if cats_represented >= 3:
        skills_score = min(100.0, skills_score + 5.0)
    skills_score = round(min(100.0, skills_score), 1)

    # 3. Formatting Score (0-100)
    fmt_points = 0
    words = parsed_data.get('word_count', 0)
    # Ideal resume length is 350 - 950 words
    if 300 <= words <= 1200:
        fmt_points += 40
    elif 150 <= words < 300 or 1200 < words <= 1800:
        fmt_points += 25
    else:
        fmt_points += 10

    # Section headers clarity
    if len(present_sections) >= 4:
        fmt_points += 35
    elif len(present_sections) >= 2:
        fmt_points += 20
    else:
        fmt_points += 10

    # Readability / Non-garbled text check
    non_ascii_ratio = len(re.findall(r'[^\x00-\x7F]', raw_text)) / max(1, len(raw_text))
    if non_ascii_ratio < 0.05:
        fmt_points += 25
    else:
        fmt_points += 10

    formatting_score = float(fmt_points)

    # 4. Keyword Score (0-100)
    action_verbs_found = parsed_data.get('action_verbs', [])
    verb_count = len(action_verbs_found)
    verb_pts = min(50.0, verb_count * 7.0)

    # Tech keyword density
    kw_pts = min(50.0, skill_count * 4.0)
    keyword_score = round(min(100.0, verb_pts + kw_pts), 1)

    # 5. Content Quality Score (0-100)
    # Metrics, numbers, percentages ($50k, 25%, 3x, 100+)
    metrics_found = len(re.findall(r'\b\d+(?:\.\d+)?%|\$\d+(?:,\d+)*(?:\.\d+)?|\b\d+\+\b|\b\d+x\b', raw_text))
    metric_pts = min(40.0, metrics_found * 10.0)

    # Bullet points structure
    bullets = len(re.findall(r'^[•\-\*]\s+', raw_text, re.MULTILINE))
    bullet_pts = min(30.0, bullets * 3.0)

    # Summary depth
    summary_len = len(parsed_data.get('sections', {}).get('summary', '').split())
    sum_pts = 30.0 if summary_len >= 20 else (15.0 if summary_len > 0 else 5.0)

    content_quality_score = round(min(100.0, metric_pts + bullet_pts + sum_pts), 1)

    # Overall ATS Weighted Score
    ats_score = round(
        (0.25 * completeness_score) +
        (0.25 * skills_score) +
        (0.20 * keyword_score) +
        (0.15 * content_quality_score) +
        (0.15 * formatting_score),
        1
    )

    return {
        'ats_score': ats_score,
        'skills_score': skills_score,
        'formatting_score': formatting_score,
        'keyword_score': keyword_score,
        'content_quality_score': content_quality_score,
        'completeness_score': completeness_score,
        'metrics_count': metrics_found,
        'action_verbs_count': verb_count
    }


def perform_full_analysis(raw_text: str, parsed_data: dict, gemini_api_key: str = None) -> dict:
    """
    Executes full ATS scoring, rule verification, and Gemini deep qualitative critique.
    """
    scores = calculate_ats_scores(parsed_data, raw_text)
    ai_service = AIService(api_key=gemini_api_key)
    ai_feedback = ai_service.analyze_resume_deep(raw_text, parsed_data)

    return {
        'scores': scores,
        'strengths': ai_feedback.get('strengths', []),
        'weaknesses': ai_feedback.get('weaknesses', []),
        'recommendations': ai_feedback.get('recommendations', []),
        'summary_critique': ai_feedback.get('summary_critique', ''),
        'formatting_critique': ai_feedback.get('formatting_critique', ''),
        'suggested_action_verbs': ai_feedback.get('suggested_action_verbs', []),
        'action_verbs_found': parsed_data.get('action_verbs', [])
    }


def generate_pdf_report(analysis_obj, output_path: str):
    """
    Generates a PDF analysis report using ReportLab.
    """
    doc = SimpleDocTemplate(output_path, pagesize=letter, rightMargin=36, leftMargin=36, topMargin=36, bottomMargin=36)
    styles = getSampleStyleSheet()

    # Custom styles
    title_style = ParagraphStyle(
        'RepTitle',
        parent=styles['Heading1'],
        fontName='Helvetica-Bold',
        fontSize=22,
        textColor=colors.HexColor('#0F172A'),
        spaceAfter=10
    )
    subtitle_style = ParagraphStyle(
        'RepSubtitle',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=11,
        textColor=colors.HexColor('#64748B'),
        spaceAfter=15
    )
    heading_style = ParagraphStyle(
        'RepHeading',
        parent=styles['Heading2'],
        fontName='Helvetica-Bold',
        fontSize=14,
        textColor=colors.HexColor('#4338CA'),
        spaceBefore=12,
        spaceAfter=6
    )
    body_style = ParagraphStyle(
        'RepBody',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=10,
        textColor=colors.HexColor('#334155'),
        spaceAfter=6
    )
    bullet_style = ParagraphStyle(
        'RepBullet',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=10,
        textColor=colors.HexColor('#1E293B'),
        leftIndent=15,
        spaceAfter=4
    )

    story = []

    # Header
    story.append(Paragraph("AI Resume Analyzer & ATS Audit Report", title_style))
    date_str = datetime.utcnow().strftime("%B %d, %Y - %H:%M UTC")
    resume_title = analysis_obj.resume.title if analysis_obj.resume else "Uploaded Resume"
    story.append(Paragraph(f"<b>Resume:</b> {resume_title} | <b>Generated:</b> {date_str}", subtitle_style))
    story.append(HRFlowable(width="100%", thickness=1.5, color=colors.HexColor('#4338CA'), spaceAfter=15))

    # Overall Score Table
    score_data = [
        ["Metric", "Score / 100", "Rating"],
        ["Overall ATS Compatibility", f"{analysis_obj.ats_score:.1f}", "Excellent" if analysis_obj.ats_score >= 80 else ("Good" if analysis_obj.ats_score >= 60 else "Needs Work")],
        ["Skills Match & Depth", f"{analysis_obj.skills_score:.1f}", "Verified"],
        ["Formatting & Structure", f"{analysis_obj.formatting_score:.1f}", "ATS Standard"],
        ["Keywords & Action Verbs", f"{analysis_obj.keyword_score:.1f}", "Analyzed"],
        ["Content Quality & Metrics", f"{analysis_obj.content_quality_score:.1f}", "Audited"],
        ["Resume Completeness", f"{analysis_obj.completeness_score:.1f}", "Audited"]
    ]

    score_table = Table(score_data, colWidths=[240, 120, 160])
    score_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#0F172A')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ('TOPPADDING', (0, 0), (-1, -1), 6),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#CBD5E1')),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.HexColor('#F8FAFC'), colors.white])
    ]))
    story.append(score_table)
    story.append(Spacer(1, 15))

    # Strengths
    strengths = analysis_obj.get_strengths()
    if strengths:
        story.append(Paragraph("Key Strengths", heading_style))
        for s in strengths:
            story.append(Paragraph(f"• <b>+</b> {s}", bullet_style))
        story.append(Spacer(1, 10))

    # Weaknesses
    weaknesses = analysis_obj.get_weaknesses()
    if weaknesses:
        story.append(Paragraph("Areas for Improvement", heading_style))
        for w in weaknesses:
            story.append(Paragraph(f"• <b>-</b> {w}", bullet_style))
        story.append(Spacer(1, 10))

    # Recommendations
    recommendations = analysis_obj.get_recommendations()
    if recommendations:
        story.append(Paragraph("Actionable Recommendations", heading_style))
        for r in recommendations:
            story.append(Paragraph(f"• {r}", bullet_style))
        story.append(Spacer(1, 10))

    # Action Verbs
    verbs = analysis_obj.get_action_verbs()
    if verbs:
        story.append(Paragraph("Action Verbs Detected", heading_style))
        verb_text = ", ".join(verbs)
        story.append(Paragraph(f"<b>Verbs found:</b> {verb_text}", body_style))

    doc.build(story)
    return output_path
