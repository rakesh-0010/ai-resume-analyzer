import os
import tempfile
import pymupdf
import docx
from app.resume_parser import (
    extract_text_from_pdf,
    extract_text_from_docx,
    extract_contact_info,
    split_into_sections,
    extract_skills,
    find_action_verbs,
    parse_resume
)


SAMPLE_RESUME_TEXT = """
Sarah Connor
Email: sarah.connor@cyberdyne.io | Phone: +1-555-019-2834 | linkedin.com/in/sarah-connor | github.com/sconnor
San Francisco, CA

PROFESSIONAL SUMMARY
Dynamic Senior Full Stack Engineer with 6+ years designing high-concurrency microservices, data pipelines, and responsive web applications. Proven track record improving system uptime and developer velocity.

TECHNICAL SKILLS
Languages: Python, JavaScript, TypeScript, SQL, HTML, CSS, Bash
Frameworks: Flask, Django, React, Bootstrap, Pandas, NumPy
Databases: MySQL, PostgreSQL, Redis, MongoDB
DevOps & Cloud: AWS, Docker, Kubernetes, Git, CI/CD, Linux

WORK EXPERIENCE
Lead Systems Engineer | Skynet Systems | 2022 - Present
• Spearheaded migration of monolithic platform to Python Flask microservices on AWS Docker clusters.
• Architected Redis caching layer, decreasing p99 database latency by 45%.
• Optimized MySQL query execution plans, improving throughput by 30%.
• Mentored 8 junior and mid-level engineers in test-driven development and clean code practices.

Software Engineer | Cyberdyne Systems | 2019 - 2022
• Developed REST APIs in Flask and Python for automated document analysis.
• Engineered real-time notification engine supporting 50,000 active concurrent connections.

EDUCATION
B.S. in Computer Science | Stanford University | 2015 - 2019 | GPA: 3.8 / 4.0

PROJECTS
Cloud Task Orchestrator | Python, Celery, Redis
• Built distributed task scheduler handling 1M background jobs daily.

CERTIFICATIONS
AWS Certified Solutions Architect
"""


def test_contact_info_extraction():
    """Verify email, phone, links, and name extraction."""
    contact = extract_contact_info(SAMPLE_RESUME_TEXT)
    assert contact['email'] == 'sarah.connor@cyberdyne.io'
    assert '555' in contact['phone']
    assert 'linkedin.com/in/sarah-connor' in contact['linkedin']
    assert 'github.com/sconnor' in contact['github']
    assert contact['name'] == 'Sarah Connor'


def test_section_splitting():
    """Verify sections are partitioned correctly."""
    sections = split_into_sections(SAMPLE_RESUME_TEXT)
    assert 'summary' in sections
    assert 'skills' in sections
    assert 'experience' in sections
    assert 'education' in sections
    assert 'projects' in sections
    assert 'Python' in sections['skills']
    assert 'Stanford' in sections['education']


def test_skills_extraction():
    """Verify technical skills detection and categorization."""
    skills = extract_skills(SAMPLE_RESUME_TEXT)
    assert skills['total_count'] >= 10
    assert 'python' in skills['all']
    assert 'flask' in skills['all']
    assert 'mysql' in skills['all']
    assert 'docker' in skills['all']
    assert 'Languages' in skills['categorized']
    assert 'Databases' in skills['categorized']


def test_action_verbs_extraction():
    """Verify strong action verbs are identified."""
    verbs = find_action_verbs(SAMPLE_RESUME_TEXT)
    assert 'spearheaded' in verbs
    assert 'architected' in verbs
    assert 'optimized' in verbs
    assert 'engineered' in verbs


def test_pdf_extraction(tmp_path):
    """Create a temporary PDF and test PyMuPDF extraction."""
    pdf_path = str(tmp_path / "test_resume.pdf")
    doc = pymupdf.open()
    page = doc.new_page()
    page.insert_text((50, 50), SAMPLE_RESUME_TEXT)
    doc.save(pdf_path)
    doc.close()

    extracted = extract_text_from_pdf(pdf_path)
    assert "Sarah Connor" in extracted
    assert "sarah.connor@cyberdyne.io" in extracted


def test_docx_extraction(tmp_path):
    """Create a temporary DOCX and test python-docx extraction."""
    docx_path = str(tmp_path / "test_resume.docx")
    doc = docx.Document()
    for line in SAMPLE_RESUME_TEXT.split('\n'):
        if line.strip():
            doc.add_paragraph(line)
    doc.save(docx_path)

    extracted = extract_text_from_docx(docx_path)
    assert "Sarah Connor" in extracted
    assert "Skynet Systems" in extracted


def test_full_parse_resume():
    """Test full pipeline parse_resume structure."""
    result = parse_resume(SAMPLE_RESUME_TEXT)
    assert result['word_count'] > 100
    assert 'experience' in result['present_sections']
    assert 'education' in result['present_sections']
    assert result['contact']['email'] is not None
