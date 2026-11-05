from app.ai_service import AIService


JOB_DESCRIPTION_TEXT = """
We are looking for a Senior Python Backend Engineer with strong expertise in:
- Python, Flask or Django
- MySQL and Redis database design
- Docker and Kubernetes container deployment
- AWS cloud infrastructure
- GraphQL or REST APIs
Bonus if you have experience with Kafka or Celery.
"""


def test_job_description_matching():
    """Test skill extraction and matching against job requirements."""
    ai_service = AIService()
    resume_skills = ['python', 'flask', 'mysql', 'docker', 'aws']
    resume_text = "Experienced in Python, Flask, MySQL, Docker, and AWS."

    result = ai_service.match_job_description(
        resume_text=resume_text,
        resume_skills=resume_skills,
        job_text=JOB_DESCRIPTION_TEXT
    )

    assert 'compatibility_score' in result
    assert result['compatibility_score'] > 40.0
    assert 'Python' in result['matching_skills'] or 'python' in [s.lower() for s in result['matching_skills']]
    assert 'Flask' in result['matching_skills'] or 'flask' in [s.lower() for s in result['matching_skills']]
    assert len(result['missing_skills']) > 0  # e.g., Kubernetes, Kafka, etc.


def test_ai_rewrite_heuristic():
    """Test AI content rewrite functionality (with fallback)."""
    ai_service = AIService()
    draft = "responsible for writing code and fixing bugs on database"
    result = ai_service.rewrite_content('Work Experience Bullet Points', draft, 'Software Engineer')

    assert 'improved_content' in result
    assert len(result['improved_content']) > 10
    assert 'key_changes' in result
    assert 'action_verbs_used' in result
