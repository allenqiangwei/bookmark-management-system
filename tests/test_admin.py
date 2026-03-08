"""Tests for admin bookmark management."""
import pytest
from app import create_app, db
from models import Bookmark, Group, User


@pytest.fixture
def app():
    """Create application for testing."""
    app = create_app({
        'TESTING': True,
        'SQLALCHEMY_DATABASE_URI': 'sqlite:///:memory:',
        'WTF_CSRF_ENABLED': False
    })

    with app.app_context():
        db.create_all()
        # Create test user and groups
        user = User(username='testadmin', is_admin=True)
        user.set_password('password')
        db.session.add(user)
        db.session.commit()

        group1 = Group(name='Development', user_id=user.id, order=1)
        group2 = Group(name='Design', user_id=user.id, order=2)
        db.session.add_all([group1, group2])
        db.session.commit()

    yield app

    with app.app_context():
        db.drop_all()


@pytest.fixture
def client(app):
    """Create test client with logged-in admin user."""
    client = app.test_client()

    # Log in as admin
    with app.app_context():
        user = User.query.filter_by(username='testadmin').first()

    with client.session_transaction() as sess:
        sess['_user_id'] = str(user.id)

    return client


def test_admin_bookmarks_page(client):
    """Test admin bookmarks page loads."""
    response = client.get('/admin/bookmarks')
    assert response.status_code == 200
    assert b'Bookmark Management' in response.data


def test_create_bookmark(app, client):
    """Test creating a new bookmark."""
    with app.app_context():
        user = User.query.first()
        group = Group.query.first()
        user_id = user.id
        group_id = group.id

    response = client.post('/admin/bookmarks/create', data={
        'title': 'GitHub',
        'url': 'https://github.com',
        'user_id': user_id,
        'group_id': group_id
    }, follow_redirects=True)

    assert response.status_code == 200

    with app.app_context():
        bookmark = Bookmark.query.filter_by(title='GitHub').first()
        assert bookmark is not None
        assert bookmark.url == 'https://github.com'
        assert bookmark.user_id == user_id
        assert bookmark.group_id == group_id


def test_update_bookmark(app, client):
    """Test updating an existing bookmark."""
    with app.app_context():
        user = User.query.first()
        group = Group.query.first()
        bookmark = Bookmark(
            title='Old Title',
            url='https://old.com',
            user_id=user.id,
            group_id=group.id,
            order=1
        )
        db.session.add(bookmark)
        db.session.commit()
        bookmark_id = bookmark.id
        group_id = group.id

    response = client.post(f'/admin/bookmarks/{bookmark_id}/update', data={
        'title': 'New Title',
        'url': 'https://new.com',
        'group_id': group_id
    }, follow_redirects=True)

    assert response.status_code == 200

    with app.app_context():
        bookmark = Bookmark.query.get(bookmark_id)
        assert bookmark.title == 'New Title'
        assert bookmark.url == 'https://new.com'


def test_delete_bookmark(app, client):
    """Test deleting a bookmark."""
    with app.app_context():
        user = User.query.first()
        group = Group.query.first()
        bookmark = Bookmark(
            title='To Delete',
            url='https://delete.com',
            user_id=user.id,
            group_id=group.id,
            order=1
        )
        db.session.add(bookmark)
        db.session.commit()
        bookmark_id = bookmark.id

    response = client.post(f'/admin/bookmarks/{bookmark_id}/delete', follow_redirects=True)
    assert response.status_code == 200

    with app.app_context():
        bookmark = Bookmark.query.get(bookmark_id)
        assert bookmark is None


def test_reorder_bookmarks(app, client):
    """Test reordering bookmarks."""
    with app.app_context():
        user = User.query.first()
        group = Group.query.first()
        b1 = Bookmark(title='First', url='https://1.com', user_id=user.id, group_id=group.id, order=1)
        b2 = Bookmark(title='Second', url='https://2.com', user_id=user.id, group_id=group.id, order=2)
        b3 = Bookmark(title='Third', url='https://3.com', user_id=user.id, group_id=group.id, order=3)
        db.session.add_all([b1, b2, b3])
        db.session.commit()
        id1, id2, id3 = b1.id, b2.id, b3.id

    # Reorder: [3, 1, 2]
    response = client.post('/admin/bookmarks/reorder',
                          json={'order': [id3, id1, id2]})
    assert response.status_code == 200

    with app.app_context():
        b1 = Bookmark.query.get(id1)
        b2 = Bookmark.query.get(id2)
        b3 = Bookmark.query.get(id3)
        assert b3.order == 1
        assert b1.order == 2
        assert b2.order == 3
