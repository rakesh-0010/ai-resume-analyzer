import io
from app.models import Resume, ResumeAnalysis
from app.database import db
from tests.test_parser import SAMPLE_RESUME_TEXT


def test_dashboard_route(auth_client):
    """Test dashboard is accessible for logged-in user."""
    response = auth_client.get('/dashboard')
    assert response.status_code == 200
    assert b'Uploaded Resumes' in response.data


def test_resume_upload_route(auth_client, app, test_user):
    """Test uploading a text-based resume file."""
    data = {
        'title': 'Test Full Stack Resume',
        'resume_file': (io.BytesIO(SAMPLE_RESUME_TEXT.encode('utf-8')), 'resume.pdf')
    }
    # Note: For testing file upload through PyMuPDF, let's create a valid minimal PDF in-memory
    import pymupdf
    doc = pymupdf.open()
    page = doc.new_page()
    page.insert_text((50, 50), SAMPLE_RESUME_TEXT)
    pdf_bytes = doc.tobytes()
    doc.close()

    response = auth_client.post('/resume/upload', data={
        'title': 'Test Full Stack Resume',
        'resume_file': (io.BytesIO(pdf_bytes), 'resume.pdf')
    }, content_type='multipart/form-data', follow_redirects=True)

    assert response.status_code == 200
    with app.app_context():
        resumes = Resume.query.filter_by(user_id=test_user.id).all()
        assert len(resumes) >= 1
        assert resumes[0].title == 'Test Full Stack Resume'
        assert resumes[0].analyses is not None
        assert len(resumes[0].analyses) >= 1


def test_resume_builder_create(auth_client, app, test_user):
    """Test building a resume through the builder form creates a valid PDF."""
    response = auth_client.post('/resume-builder/create', data={
        'full_name': 'Alex Rivera',
        'email': 'alex.rivera@example.com',
        'phone': '555-123-4567',
        'location': 'Seattle, WA',
        'summary': 'Dedicated engineer with experience in cloud software.',
        'skills': 'Python, Flask, MySQL, Docker',
        'template': 'modern-tech',
        'exp_role[]': ['Cloud Developer'],
        'exp_company[]': ['Tech Corp'],
        'exp_duration[]': ['2023 - Present'],
        'exp_location[]': ['Remote'],
        'exp_description[]': ['• Scaled database throughput by 20%.'],
        'edu_degree[]': ['B.S. in Software Engineering'],
        'edu_school[]': ['University of Washington'],
        'edu_year[]': ['2023'],
        'edu_score[]': ['3.9']
    }, follow_redirects=True)

    assert response.status_code == 200
    with app.app_context():
        resumes = Resume.query.filter_by(user_id=test_user.id).all()
        built_resumes = [r for r in resumes if 'Built Resume' in r.title]
        assert len(built_resumes) >= 1


def test_admin_dashboard_authorization(client, test_user, test_admin):
    """Test regular users cannot access admin dashboard, but admins can."""
    # 1. Login as regular user
    client.post('/login', data={'email': test_user.email, 'password': 'SecurePassword123'}, follow_redirects=True)
    resp = client.get('/admin/dashboard', follow_redirects=True)
    assert b'Access restricted to administrators' in resp.data

    # 2. Login as admin user
    client.get('/logout', follow_redirects=True)
    client.post('/login', data={'email': test_admin.email, 'password': 'AdminPassword123'}, follow_redirects=True)
    resp = client.get('/admin/dashboard', follow_redirects=True)
    assert resp.status_code == 200
    assert b'System Administration & Overview' in resp.data
