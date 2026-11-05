import pytest
import os
import shutil
import tempfile
from app import create_app
from app.database import db
from app.models import User, Resume, ResumeAnalysis
from config import TestConfig


@pytest.fixture
def app():
    test_upload_dir = tempfile.mkdtemp()
    test_report_dir = tempfile.mkdtemp()

    class CustomTestConfig(TestConfig):
        UPLOAD_FOLDER = test_upload_dir
        REPORT_FOLDER = test_report_dir

    app = create_app(CustomTestConfig)

    with app.app_context():
        db.create_all()
        yield app
        db.session.remove()
        db.drop_all()

    # Clean temporary directories
    shutil.rmtree(test_upload_dir, ignore_errors=True)
    shutil.rmtree(test_report_dir, ignore_errors=True)


@pytest.fixture
def client(app):
    return app.test_client()


@pytest.fixture
def runner(app):
    return app.test_cli_runner()


@pytest.fixture
def test_user(app):
    user = User(
        name="Test Candidate",
        email="candidate@example.com",
        role="user"
    )
    user.set_password("SecurePassword123")
    db.session.add(user)
    db.session.commit()
    return user


@pytest.fixture
def test_admin(app):
    admin = User(
        name="Admin User",
        email="admin@example.com",
        role="admin"
    )
    admin.set_password("AdminPassword123")
    db.session.add(admin)
    db.session.commit()
    return admin


@pytest.fixture
def auth_client(client, test_user):
    client.post('/login', data={
        'email': 'candidate@example.com',
        'password': 'SecurePassword123'
    }, follow_redirects=True)
    return client
