"""Tests for frontend routes."""
import pytest
from app import create_app, db
from models import User, Bookmark, Group


@pytest.fixture
def app():
    """Create test application."""
    app = create_app({
        'TESTING': True,
        'SQLALCHEMY_DATABASE_URI': 'sqlite:///:memory:',
        'WTF_CSRF_ENABLED': False,
        'SECRET_KEY': 'test-secret-key'
    })

    with app.app_context():
        db.create_all()
        yield app
        db.session.remove()
        db.drop_all()


@pytest.fixture
def client(app):
    """Create test client."""
    return app.test_client()


@pytest.fixture
def auth_user(app, client):
    """Create and authenticate a user."""
    with app.app_context():
        user = User(username='testuser')
        user.set_password('password123')
        db.session.add(user)
        db.session.commit()
        user_id = user.id

    # Log in the user
    client.post('/auth/login', data={
        'username': 'testuser',
        'password': 'password123'
    })

    with app.app_context():
        return User.query.get(user_id)


def test_dashboard_requires_login(client):
    """Test that dashboard requires authentication."""
    response = client.get('/dashboard')
    assert response.status_code == 302
    assert '/auth/login' in response.location


def test_dashboard_displays_bookmarks(app, client, auth_user):
    """Test that dashboard displays user's bookmarks."""
    with app.app_context():
        # Create a group
        group = Group(name='Work', user_id=auth_user.id)
        db.session.add(group)
        db.session.commit()
        group_id = group.id

        # Create bookmarks
        bookmark1 = Bookmark(
            url='https://example.com',
            title='Example Site',
            user_id=auth_user.id,
            group_id=group_id
        )
        bookmark2 = Bookmark(
            url='https://github.com',
            title='GitHub',
            user_id=auth_user.id
        )
        db.session.add(bookmark1)
        db.session.add(bookmark2)
        db.session.commit()

    response = client.get('/dashboard')
    assert response.status_code == 200
    assert b'Example Site' in response.data
    assert b'GitHub' in response.data
    assert b'Work' in response.data
