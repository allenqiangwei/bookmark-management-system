import pytest
from app import create_app, db
from models import User

@pytest.fixture
def app():
    """创建测试应用"""
    app = create_app({
        'TESTING': True,
        'SQLALCHEMY_DATABASE_URI': 'sqlite:///:memory:',
        'WTF_CSRF_ENABLED': False,
        'SECRET_KEY': 'test-secret-key'
    })

    with app.app_context():
        db.create_all()

        # 创建测试用户
        user = User(username='testuser', is_admin=False)
        user.set_password('password123')
        db.session.add(user)
        db.session.commit()

        yield app

        db.session.remove()
        db.drop_all()

@pytest.fixture
def client(app):
    """创建测试客户端"""
    return app.test_client()

def test_login_success(client):
    """测试登录成功"""
    response = client.post('/auth/login', data={
        'username': 'testuser',
        'password': 'password123'
    }, follow_redirects=False)

    # 登录成功应该返回302重定向
    assert response.status_code == 302
    assert '/auth/login' not in response.location

def test_login_failure(client):
    """测试登录失败"""
    response = client.post('/auth/login', data={
        'username': 'testuser',
        'password': 'wrongpassword'
    })

    # 登录失败应该返回200，并且不应该重定向
    assert response.status_code == 200

def test_logout(client):
    """测试登出"""
    # 先登录
    client.post('/auth/login', data={
        'username': 'testuser',
        'password': 'password123'
    })

    # 登出
    response = client.get('/auth/logout', follow_redirects=False)
    # 登出应该返回302重定向到登录页面
    assert response.status_code == 302
    assert '/auth/login' in response.location
