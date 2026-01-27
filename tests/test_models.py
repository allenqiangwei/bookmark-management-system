import pytest
from app import create_app, db
from models import User, Group, Bookmark
import bcrypt

@pytest.fixture
def app():
    """创建测试应用"""
    config_overrides = {
        'TESTING': True,
        'SQLALCHEMY_DATABASE_URI': 'sqlite:///:memory:'
    }

    app = create_app(config_overrides)

    with app.app_context():
        db.create_all()
        yield app
        db.session.remove()
        db.drop_all()

@pytest.fixture
def client(app):
    """创建测试客户端"""
    return app.test_client()

def test_user_password_hashing(app):
    """测试用户密码哈希"""
    with app.app_context():
        user = User(username='testuser', is_admin=False)
        user.set_password('password123')

        assert user.password_hash is not None
        assert user.check_password('password123')
        assert not user.check_password('wrongpassword')

def test_user_creation(app):
    """测试用户创建"""
    with app.app_context():
        user = User(username='admin', is_admin=True)
        user.set_password('admin123')
        db.session.add(user)
        db.session.commit()

        found_user = User.query.filter_by(username='admin').first()
        assert found_user is not None
        assert found_user.username == 'admin'
        assert found_user.is_admin is True
