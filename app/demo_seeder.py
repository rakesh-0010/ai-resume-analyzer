import os
import json
from datetime import datetime
from app.database import db
from app.models import User, Resume, ResumeAnalysis, JobDescription, AnalysisHistory, ResumeTemplate
from app.resume_parser import parse_resume

SAMPLE_CANDIDATE_RESUME_TEXT = """Alex Rivera
Email: demo.candidate@ats-pro.ai | Phone: +1-555-234-5678 | San Francisco, CA
LinkedIn: linkedin.com/in/alex-rivera-demo | GitHub: github.com/alexrivera-demo | Portfolio: alexrivera.dev

PROFESSIONAL SUMMARY
Senior Full Stack & Python Backend Engineer with 5+ years of experience engineering high-throughput microservices, cloud architectures, and database layers. Adept at scaling transactional workloads, optimizing query execution, and accelerating continuous delivery pipelines.

TECHNICAL SKILLS
• Languages: Python, JavaScript, TypeScript, SQL, HTML5, CSS3, Bash
• Frameworks & Libraries: Flask, Django, FastAPI, React, Node.js, Bootstrap, Pandas, NumPy
• Databases & Storage: MySQL, PostgreSQL, Redis, MongoDB
• Cloud & DevOps: AWS (EC2, S3, RDS), Docker, Kubernetes, CI/CD, Git, Linux, Nginx
• Methodologies & Tools: RESTful APIs, Microservices, Agile/Scrum, Pytest, Jira

PROFESSIONAL EXPERIENCE
Senior Software Engineer | CloudScale Systems | 2022 - Present
• Spearheaded the redesign of core backend payment ingestion service using Python Flask and Redis, handling 25,000+ requests per second.
• Optimized MySQL database indexing and caching architectures, decreasing p99 query latency by 42%.
• Engineered automated CI/CD deployment pipelines using Docker and GitHub Actions, cutting production release cycles from 3 hours to 18 minutes.
• Mentored 6 software engineers across test automation, clean architecture, and system observability.

Software Developer | DataStream Technologies | 2020 - 2022
• Developed distributed RESTful APIs in Python and Flask supporting 1.2M monthly active dashboard users.
• Orchestrated event-driven microservices architecture communicating via Redis message broker.
• Standardized unit and integration testing suite using Pytest, boosting code coverage from 58% to 91%.

EDUCATION
Bachelor of Science in Computer Science | University of California, Berkeley | 2016 - 2020
• Honors: Magna Cum Laude | GPA: 3.85 / 4.0

KEY PROJECTS
• Distributed Job Queue Engine (Python, Flask, Redis, Docker): Open-source asynchronous task processor executing 500k background jobs daily with 99.99% reliability.
• Real-time Analytics Visualizer (Flask, MySQL, Chart.js): Live telemetry dashboard tracking cluster health, throughput, and error rates.

CERTIFICATIONS
• AWS Certified Solutions Architect - Associate
• Certified Kubernetes Application Developer (CKAD)
"""


def seed_demo_accounts(app):
    """
    Ensures pre-configured Demo Candidate and Demo Admin accounts
    exist with rich sample data for immediate 1-click test drive.
    """
    with app.app_context():
        # 1. Candidate Demo Account
        candidate = User.query.filter_by(email='demo.candidate@ats-pro.ai').first()
        if not candidate:
            candidate = User(
                name="Alex Rivera (Demo Candidate)",
                email="demo.candidate@ats-pro.ai",
                role="user",
                phone="+1 (555) 234-5678",
                target_role="Senior Full Stack Engineer",
                bio="Senior Full Stack & Python Engineer with 5+ years engineering high-concurrency microservices, MySQL databases, and cloud architectures."
            )
            candidate.set_password("Password123!")
            db.session.add(candidate)
            db.session.flush()

            # Create sample resume file
            upload_dir = app.config['UPLOAD_FOLDER']
            os.makedirs(upload_dir, exist_ok=True)
            resume_file_path = os.path.join(upload_dir, f"demo_alex_rivera_resume.txt")
            with open(resume_file_path, "w", encoding="utf-8") as f:
                f.write(SAMPLE_CANDIDATE_RESUME_TEXT)

            parsed = parse_resume(SAMPLE_CANDIDATE_RESUME_TEXT)

            resume = Resume(
                user_id=candidate.id,
                title="Senior Full Stack & Cloud Resume (Demo)",
                filename="Alex_Rivera_Senior_FullStack.pdf",
                file_path=resume_file_path,
                file_type="pdf",
                file_size=len(SAMPLE_CANDIDATE_RESUME_TEXT.encode('utf-8')),
                raw_text=SAMPLE_CANDIDATE_RESUME_TEXT
            )
            resume.parsed = parsed
            db.session.add(resume)
            db.session.flush()

            # Create ATS Analysis
            strengths = [
                "Exceptional technical breadth with 18+ industry-recognized competencies across Languages, Frameworks, Databases, and DevOps.",
                "Robust quantifiable accomplishments (e.g., 25,000 req/sec, 42% latency reduction, 18-minute deploys).",
                "Strong executive action verbs utilized consistently across all bullet points (Spearheaded, Optimized, Engineered, Orchestrated).",
                "Complete contact information with email, phone, LinkedIn, GitHub, and portfolio URLs."
            ]
            weaknesses = [
                "Could benefit from highlighting public cloud cost reduction metrics ($ amount saved).",
                "Expand on cross-functional product leadership accomplishments."
            ]
            recommendations = [
                "Add specific dollar figures or infrastructure cost percentages saved during MySQL and Redis optimization.",
                "Highlight familiarity with AI model integration (Gemini, LangChain) given your backend background.",
                "Tailor resume summary headline to exact job titles when applying for Staff or Lead roles."
            ]

            analysis = ResumeAnalysis(
                resume_id=resume.id,
                user_id=candidate.id,
                ats_score=88.5,
                skills_score=94.0,
                formatting_score=92.0,
                keyword_score=87.0,
                content_quality_score=85.0,
                completeness_score=96.0,
                detailed_feedback=json.dumps({"word_count": parsed['word_count']}),
                recommendations=json.dumps(recommendations),
                strengths=json.dumps(strengths),
                weaknesses=json.dumps(weaknesses),
                action_verbs_found=json.dumps(parsed.get('action_verbs', []))
            )
            db.session.add(analysis)
            db.session.flush()

            # Create History Record
            history = AnalysisHistory(
                user_id=candidate.id,
                resume_id=resume.id,
                analysis_id=analysis.id,
                action_type="full_analysis",
                ats_score=88.5,
                summary="Full ATS Audit of Senior Full Stack & Cloud Resume: 88.5/100"
            )
            db.session.add(history)

            # Create Job Match Record
            job = JobDescription(
                user_id=candidate.id,
                resume_id=resume.id,
                title="Lead Backend Architect",
                company="FinTech Stripe Systems",
                raw_text="Seeking Senior/Lead Backend Python Engineer experienced in Flask, MySQL, Redis, AWS, and Docker.",
                required_skills=json.dumps(["Python", "Flask", "MySQL", "Redis", "AWS", "Docker", "Kubernetes", "GraphQL"]),
                matching_skills=json.dumps(["Python", "Flask", "MySQL", "Redis", "AWS", "Docker", "Kubernetes"]),
                missing_skills=json.dumps(["GraphQL"]),
                compatibility_score=87.5,
                recommendations=json.dumps([
                    "You cover 7 out of 8 required technologies (87.5% match).",
                    "Add hands-on exposure with GraphQL schema definition in the Skills section."
                ])
            )
            db.session.add(job)

        # 2. Admin Demo Account
        admin = User.query.filter_by(email='demo.admin@ats-pro.ai').first()
        if not admin:
            admin = User(
                name="Demo Administrator",
                email="demo.admin@ats-pro.ai",
                role="admin",
                phone="+1 (555) 999-0000",
                target_role="Platform Administrator",
                bio="System administrator managing platform analytics, users, and ATS optimization telemetry."
            )
            admin.set_password("AdminPassword123!")
            db.session.add(admin)

        # Ensure default templates exist
        if ResumeTemplate.query.count() == 0:
            t1 = ResumeTemplate(name='Classic ATS', slug='classic-ats', description='Single column, highly readable font hierarchy, timeless ATS standard.')
            t2 = ResumeTemplate(name='Modern Tech', slug='modern-tech', description='Indigo accent bars, clean developer skill blocks, optimized for engineering.')
            t3 = ResumeTemplate(name='Minimalist Executive', slug='minimalist-executive', description='Streamlined slate design, refined dividers, high executive impact.')
            db.session.add_all([t1, t2, t3])

        db.session.commit()
