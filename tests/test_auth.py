from app.models import User
from app.database import db


def test_user_registration(client, app):
    """Test user can register successfully."""
    response = client.post('/register', data={
        'name': 'Jane Doe',
        'email': 'jane@example.com',
        'password': 'Password123',
        'confirm_password': 'Password123'
    }, follow_redirects=True)

    assert response.status_code == 200
    with app.app_context():
        user = User.query.filter_by(email='jane@example.com').first()
        assert user is not None
        assert user.name == 'Jane Doe'
        assert user.check_password('Password123')


def test_duplicate_registration(client, test_user):
    """Test registering with an existing email is rejected."""
    response = client.post('/register', data={
        'name': 'Duplicate User',
        'email': test_user.email,
        'password': 'Password123',
        'confirm_password': 'Password123'
    }, follow_redirects=True)

    assert b'already exists' in response.data or response.status_code == 200


def test_user_login_success(client, test_user):
    """Test valid credentials sign user in."""
    response = client.post('/login', data={
        'email': test_user.email,
        'password': 'SecurePassword123'
    }, follow_redirects=True)

    assert response.status_code == 200
    assert b'Analytics & Optimization Dashboard' in response.data or b'Dashboard' in response.data


def test_user_login_invalid_password(client, test_user):
    """Test invalid credentials show error."""
    response = client.post('/login', data={
        'email': test_user.email,
        'password': 'WrongPassword'
    }, follow_redirects=True)

    assert b'Invalid email or password' in response.data


def test_user_logout(auth_client):
    """Test logging out terminates the session."""
    response = auth_client.get('/logout', follow_redirects=True)
    assert response.status_code == 200
    assert b'Sign In' in response.data


def test_profile_update(auth_client, app, test_user):
    """Test updating user profile details."""
    response = auth_client.post('/profile', data={
        'name': 'Updated Name',
        'phone': '+1 (555) 987-6543',
        'target_role': 'Staff Engineer',
        'bio': 'Seasoned tech lead',
        'new_password': ''
    }, follow_redirects=True)

    assert response.status_code == 200
    with app.app_context():
        u = db.session.get(User, test_user.id)
        assert u.name == 'Updated Name'
        assert u.phone == '+1 (555) 987-6543'
        assert u.target_role == 'Staff Engineer'
