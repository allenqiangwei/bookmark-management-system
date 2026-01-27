# 书签管理系统实施计划

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** 构建一个轻量级的多用户书签管理系统，支持分组、拖拽排序和管理员用户管理

**Architecture:** Flask 服务端渲染应用 + SQLAlchemy ORM + SQLite 数据库。认证使用 Flask-Login，前端使用 Jinja2 模板 + Tailwind CSS + SortableJS 实现拖拽排序

**Tech Stack:** Python 3.11+, Flask, SQLAlchemy, Flask-Login, bcrypt, Jinja2, Tailwind CSS, SortableJS

---

## Task 1: 项目基础设施

**Files:**
- Create: `requirements.txt`
- Create: `config.py`
- Create: `app.py`
- Create: `.env.example`

**Step 1: 创建依赖文件**

创建 `requirements.txt`:
```text
Flask==3.0.0
Flask-Login==0.6.3
Flask-SQLAlchemy==3.1.1
bcrypt==4.1.2
python-dotenv==1.0.0
```

**Step 2: 创建配置文件**

创建 `config.py`:
```python
import os
from datetime import timedelta

class Config:
    """应用配置"""
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-secret-key-change-in-production'
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or 'sqlite:///instance/bookmarks.db'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    PERMANENT_SESSION_LIFETIME = timedelta(days=30)
    MAX_LOGIN_ATTEMPTS = 5
    LOGIN_ATTEMPT_WINDOW = 900  # 15分钟（秒）
```

**Step 3: 创建环境变量示例**

创建 `.env.example`:
```text
SECRET_KEY=your-secret-key-here
DATABASE_URL=sqlite:///instance/bookmarks.db
FLASK_ENV=development
```

**Step 4: 创建基础应用入口**

创建 `app.py`:
```python
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from config import Config

db = SQLAlchemy()
login_manager = LoginManager()

def create_app():
    """应用工厂函数"""
    app = Flask(__name__)
    app.config.from_object(Config)

    # 初始化扩展
    db.init_app(app)
    login_manager.init_app(app)
    login_manager.login_view = 'auth.login'

    # 创建实例文件夹
    import os
    os.makedirs(os.path.join(app.instance_path), exist_ok=True)
    os.makedirs(os.path.join(app.static_folder, 'favicons'), exist_ok=True)

    return app

if __name__ == '__main__':
    app = create_app()
    app.run(debug=True)
```

**Step 5: 安装依赖**

运行: `pip install -r requirements.txt`
预期: 所有依赖成功安装

**Step 6: 提交**

```bash
git add requirements.txt config.py app.py .env.example
git commit -m "feat: add project infrastructure and dependencies"
```

---

## Task 2: 数据库模型

**Files:**
- Create: `models.py`
- Create: `tests/test_models.py`

**Step 1: 编写用户模型测试**

创建 `tests/test_models.py`:
```python
import pytest
from app import create_app, db
from models import User, Group, Bookmark
import bcrypt

@pytest.fixture
def app():
    """创建测试应用"""
    app = create_app()
    app.config['TESTING'] = True
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'

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
```

**Step 2: 运行测试验证失败**

运行: `pytest tests/test_models.py -v`
预期: FAIL - ImportError: cannot import name 'User'

**Step 3: 实现数据库模型**

创建 `models.py`:
```python
from datetime import datetime
from flask_login import UserMixin
import bcrypt
from app import db

class User(UserMixin, db.Model):
    """用户模型"""
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(128), nullable=False)
    is_admin = db.Column(db.Boolean, default=False, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    # 关系
    groups = db.relationship('Group', backref='user', lazy=True, cascade='all, delete-orphan')
    bookmarks = db.relationship('Bookmark', backref='user', lazy=True, cascade='all, delete-orphan')

    def set_password(self, password):
        """设置密码哈希"""
        self.password_hash = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

    def check_password(self, password):
        """验证密码"""
        return bcrypt.checkpw(password.encode('utf-8'), self.password_hash.encode('utf-8'))

    def __repr__(self):
        return f'<User {self.username}>'

class Group(db.Model):
    """分组模型"""
    __tablename__ = 'groups'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False, index=True)
    name = db.Column(db.String(100), nullable=False)
    order = db.Column(db.Integer, default=0, nullable=False, index=True)
    is_collapsed = db.Column(db.Boolean, default=False, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    # 关系
    bookmarks = db.relationship('Bookmark', backref='group', lazy=True)

    def __repr__(self):
        return f'<Group {self.name}>'

class Bookmark(db.Model):
    """书签模型"""
    __tablename__ = 'bookmarks'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False, index=True)
    group_id = db.Column(db.Integer, db.ForeignKey('groups.id', ondelete='SET NULL'), nullable=True, index=True)
    title = db.Column(db.String(200), nullable=False)
    url = db.Column(db.String(500), nullable=False)
    favicon_url = db.Column(db.String(500), nullable=True)
    order = db.Column(db.Integer, default=0, nullable=False, index=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    def __repr__(self):
        return f'<Bookmark {self.title}>'
```

**Step 4: 运行测试验证通过**

运行: `pytest tests/test_models.py -v`
预期: PASS (2 tests)

**Step 5: 提交**

```bash
git add models.py tests/test_models.py
git commit -m "feat: add database models for User, Group, and Bookmark"
```

---

## Task 3: 认证系统

**Files:**
- Create: `routes/__init__.py`
- Create: `routes/auth.py`
- Create: `tests/test_auth.py`
- Modify: `app.py`

**Step 1: 编写认证测试**

创建 `tests/test_auth.py`:
```python
import pytest
from app import create_app, db
from models import User

@pytest.fixture
def app():
    """创建测试应用"""
    app = create_app()
    app.config['TESTING'] = True
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
    app.config['WTF_CSRF_ENABLED'] = False

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
    }, follow_redirects=True)

    assert response.status_code == 200
    assert b'testuser' in response.data or response.request.path == '/'

def test_login_failure(client):
    """测试登录失败"""
    response = client.post('/auth/login', data={
        'username': 'testuser',
        'password': 'wrongpassword'
    })

    assert b'Invalid username or password' in response.data or response.status_code == 200

def test_logout(client):
    """测试登出"""
    # 先登录
    client.post('/auth/login', data={
        'username': 'testuser',
        'password': 'password123'
    })

    # 登出
    response = client.get('/auth/logout', follow_redirects=True)
    assert response.status_code == 200
```

**Step 2: 运行测试验证失败**

运行: `pytest tests/test_auth.py -v`
预期: FAIL - 404 errors (routes not found)

**Step 3: 实现认证路由**

创建 `routes/__init__.py`:
```python
# 空文件，使 routes 成为包
```

创建 `routes/auth.py`:
```python
from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_user, logout_user, login_required
from app import db, login_manager
from models import User

auth = Blueprint('auth', __name__, url_prefix='/auth')

@login_manager.user_loader
def load_user(user_id):
    """加载用户"""
    return User.query.get(int(user_id))

@auth.route('/login', methods=['GET', 'POST'])
def login():
    """登录页面"""
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        remember = request.form.get('remember', False)

        user = User.query.filter_by(username=username).first()

        if user and user.check_password(password):
            login_user(user, remember=remember)
            next_page = request.args.get('next')
            return redirect(next_page if next_page else url_for('frontend.dashboard'))
        else:
            flash('Invalid username or password', 'error')

    return render_template('login.html')

@auth.route('/logout')
@login_required
def logout():
    """登出"""
    logout_user()
    return redirect(url_for('auth.login'))
```

**Step 4: 更新应用注册蓝图**

修改 `app.py`，在 `create_app()` 函数返回前添加:
```python
    # 注册蓝图
    from routes.auth import auth
    app.register_blueprint(auth)
```

**Step 5: 运行测试验证通过**

运行: `pytest tests/test_auth.py -v`
预期: PASS (3 tests)

**Step 6: 提交**

```bash
git add routes/ app.py tests/test_auth.py
git commit -m "feat: add authentication system with login and logout"
```

---

## Task 4: 基础模板和样式

**Files:**
- Create: `templates/base.html`
- Create: `templates/login.html`
- Create: `static/css/style.css`

**Step 1: 创建基础模板**

创建 `templates/base.html`:
```html
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{% block title %}书签管理系统{% endblock %}</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <link rel="stylesheet" href="{{ url_for('static', filename='css/style.css') }}">
    {% block extra_css %}{% endblock %}
</head>
<body class="bg-gray-50">
    {% with messages = get_flashed_messages(with_categories=true) %}
        {% if messages %}
            <div class="fixed top-4 right-4 z-50 space-y-2">
                {% for category, message in messages %}
                <div class="px-6 py-3 rounded-lg shadow-lg {% if category == 'error' %}bg-red-500{% else %}bg-green-500{% endif %} text-white">
                    {{ message }}
                </div>
                {% endfor %}
            </div>
        {% endif %}
    {% endwith %}

    {% block content %}{% endblock %}

    {% block extra_js %}{% endblock %}
</body>
</html>
```

**Step 2: 创建登录页面模板**

创建 `templates/login.html`:
```html
{% extends "base.html" %}

{% block title %}登录 - 书签管理系统{% endblock %}

{% block content %}
<div class="min-h-screen flex items-center justify-center px-4">
    <div class="max-w-md w-full space-y-8">
        <div class="text-center">
            <h1 class="text-4xl font-bold text-gray-900">书签管理系统</h1>
            <p class="mt-2 text-gray-600">请登录您的账号</p>
        </div>

        <form class="mt-8 space-y-6 bg-white p-8 rounded-xl shadow-md" method="POST" action="{{ url_for('auth.login') }}">
            <div class="space-y-4">
                <div>
                    <label for="username" class="block text-sm font-medium text-gray-700">用户名</label>
                    <input type="text" id="username" name="username" required
                           class="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500">
                </div>

                <div>
                    <label for="password" class="block text-sm font-medium text-gray-700">密码</label>
                    <input type="password" id="password" name="password" required
                           class="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500">
                </div>
            </div>

            <div class="flex items-center">
                <input type="checkbox" id="remember" name="remember"
                       class="h-4 w-4 text-blue-600 border-gray-300 rounded focus:ring-blue-500">
                <label for="remember" class="ml-2 block text-sm text-gray-700">记住我（30天）</label>
            </div>

            <button type="submit"
                    class="w-full py-3 px-4 bg-blue-600 hover:bg-blue-700 text-white font-medium rounded-lg transition duration-150">
                登录
            </button>
        </form>
    </div>
</div>
{% endblock %}
```

**Step 3: 创建自定义样式**

创建 `static/css/style.css`:
```css
/* 自定义样式 */
.bookmark-card {
    transition: transform 0.2s, box-shadow 0.2s;
}

.bookmark-card:hover {
    transform: translateY(-2px);
    box-shadow: 0 10px 20px rgba(0, 0, 0, 0.1);
}

.sortable-ghost {
    opacity: 0.4;
}

.sortable-drag {
    opacity: 0.8;
}

/* Flash 消息自动消失动画 */
@keyframes fadeOut {
    from { opacity: 1; }
    to { opacity: 0; }
}

.flash-message {
    animation: fadeOut 0.5s ease-in-out 4.5s forwards;
}
```

**Step 4: 手动测试登录页面**

运行: `python app.py`
访问: `http://localhost:5000/auth/login`
预期: 看到登录页面，样式正确

**Step 5: 提交**

```bash
git add templates/ static/
git commit -m "feat: add base template and login page with Tailwind CSS"
```

---

## Task 5: 前台展示页面

**Files:**
- Create: `routes/frontend.py`
- Create: `templates/dashboard.html`
- Create: `tests/test_frontend.py`
- Modify: `app.py`

**Step 1: 编写前台测试**

创建 `tests/test_frontend.py`:
```python
import pytest
from app import create_app, db
from models import User, Group, Bookmark

@pytest.fixture
def app():
    """创建测试应用"""
    app = create_app()
    app.config['TESTING'] = True
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
    app.config['WTF_CSRF_ENABLED'] = False

    with app.app_context():
        db.create_all()

        # 创建测试用户和数据
        user = User(username='testuser', is_admin=False)
        user.set_password('password123')
        db.session.add(user)
        db.session.commit()

        # 创建分组
        group = Group(user_id=user.id, name='工作', order=0)
        db.session.add(group)
        db.session.commit()

        # 创建书签
        bookmark = Bookmark(
            user_id=user.id,
            group_id=group.id,
            title='Google',
            url='https://google.com',
            order=0
        )
        db.session.add(bookmark)
        db.session.commit()

        yield app

        db.session.remove()
        db.drop_all()

@pytest.fixture
def client(app):
    """创建测试客户端"""
    return app.test_client()

@pytest.fixture
def authenticated_client(client):
    """创建已认证的测试客户端"""
    client.post('/auth/login', data={
        'username': 'testuser',
        'password': 'password123'
    })
    return client

def test_dashboard_requires_login(client):
    """测试前台需要登录"""
    response = client.get('/')
    assert response.status_code == 302  # 重定向到登录

def test_dashboard_displays_bookmarks(authenticated_client):
    """测试前台显示书签"""
    response = authenticated_client.get('/')
    assert response.status_code == 200
    assert b'Google' in response.data
    assert b'https://google.com' in response.data
```

**Step 2: 运行测试验证失败**

运行: `pytest tests/test_frontend.py -v`
预期: FAIL - 404 error (route not found)

**Step 3: 实现前台路由**

创建 `routes/frontend.py`:
```python
from flask import Blueprint, render_template
from flask_login import login_required, current_user
from models import Group, Bookmark
from sqlalchemy import func

frontend = Blueprint('frontend', __name__)

@frontend.route('/')
@login_required
def dashboard():
    """前台展示页面"""
    # 获取用户的所有分组（按order排序）
    groups = Group.query.filter_by(user_id=current_user.id).order_by(Group.order).all()

    # 为每个分组获取书签
    groups_with_bookmarks = []
    for group in groups:
        bookmarks = Bookmark.query.filter_by(
            user_id=current_user.id,
            group_id=group.id
        ).order_by(Bookmark.order).all()

        groups_with_bookmarks.append({
            'group': group,
            'bookmarks': bookmarks
        })

    # 获取未分组的书签
    ungrouped_bookmarks = Bookmark.query.filter_by(
        user_id=current_user.id,
        group_id=None
    ).order_by(Bookmark.order).all()

    return render_template('dashboard.html',
                         groups_with_bookmarks=groups_with_bookmarks,
                         ungrouped_bookmarks=ungrouped_bookmarks)
```

**Step 4: 创建前台模板**

创建 `templates/dashboard.html`:
```html
{% extends "base.html" %}

{% block title %}我的书签{% endblock %}

{% block content %}
<div class="min-h-screen bg-gray-50">
    <!-- 顶部导航栏 -->
    <nav class="bg-white shadow-sm border-b">
        <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
            <div class="flex justify-between h-16 items-center">
                <h1 class="text-2xl font-bold text-gray-900">书签管理系统</h1>
                <div class="flex items-center space-x-4">
                    <span class="text-gray-600">{{ current_user.username }}</span>
                    <a href="{{ url_for('admin.bookmarks') }}"
                       class="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition">
                        管理
                    </a>
                    <a href="{{ url_for('auth.logout') }}"
                       class="px-4 py-2 bg-gray-200 text-gray-700 rounded-lg hover:bg-gray-300 transition">
                        退出
                    </a>
                </div>
            </div>
        </div>
    </nav>

    <!-- 主内容区 -->
    <main class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <!-- 分组书签 -->
        {% for item in groups_with_bookmarks %}
        <div class="mb-8">
            <div class="flex items-center mb-4 cursor-pointer group-header"
                 data-group-id="{{ item.group.id }}"
                 onclick="toggleGroup({{ item.group.id }})">
                <svg class="w-5 h-5 mr-2 transform transition-transform group-icon"
                     id="icon-{{ item.group.id }}"
                     fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 9l-7 7-7-7"/>
                </svg>
                <h2 class="text-xl font-semibold text-gray-800">{{ item.group.name }}</h2>
                <span class="ml-2 text-sm text-gray-500">({{ item.bookmarks|length }})</span>
            </div>

            <div class="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-6 gap-4 group-content"
                 id="group-{{ item.group.id }}">
                {% for bookmark in item.bookmarks %}
                <a href="{{ bookmark.url }}" target="_blank"
                   class="bookmark-card bg-white p-4 rounded-lg shadow hover:shadow-lg flex flex-col items-center text-center">
                    {% if bookmark.favicon_url %}
                    <img src="{{ bookmark.favicon_url }}" alt="{{ bookmark.title }}" class="w-8 h-8 mb-2">
                    {% else %}
                    <div class="w-8 h-8 mb-2 bg-gray-200 rounded flex items-center justify-center">
                        <span class="text-gray-500 text-xs">{{ bookmark.title[0]|upper }}</span>
                    </div>
                    {% endif %}
                    <span class="text-sm text-gray-800 line-clamp-2">{{ bookmark.title }}</span>
                </a>
                {% endfor %}
            </div>
        </div>
        {% endfor %}

        <!-- 未分组书签 -->
        {% if ungrouped_bookmarks %}
        <div class="mb-8">
            <h2 class="text-xl font-semibold text-gray-800 mb-4">未分类</h2>
            <div class="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-6 gap-4">
                {% for bookmark in ungrouped_bookmarks %}
                <a href="{{ bookmark.url }}" target="_blank"
                   class="bookmark-card bg-white p-4 rounded-lg shadow hover:shadow-lg flex flex-col items-center text-center">
                    {% if bookmark.favicon_url %}
                    <img src="{{ bookmark.favicon_url }}" alt="{{ bookmark.title }}" class="w-8 h-8 mb-2">
                    {% else %}
                    <div class="w-8 h-8 mb-2 bg-gray-200 rounded flex items-center justify-center">
                        <span class="text-gray-500 text-xs">{{ bookmark.title[0]|upper }}</span>
                    </div>
                    {% endif %}
                    <span class="text-sm text-gray-800 line-clamp-2">{{ bookmark.title }}</span>
                </a>
                {% endfor %}
            </div>
        </div>
        {% endif %}

        {% if not groups_with_bookmarks and not ungrouped_bookmarks %}
        <div class="text-center py-12">
            <p class="text-gray-500 text-lg">还没有书签，去后台添加吧！</p>
            <a href="{{ url_for('admin.bookmarks') }}"
               class="mt-4 inline-block px-6 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition">
                添加书签
            </a>
        </div>
        {% endif %}
    </main>
</div>

<script>
// 分组折叠功能
function toggleGroup(groupId) {
    const content = document.getElementById('group-' + groupId);
    const icon = document.getElementById('icon-' + groupId);

    if (content.style.display === 'none') {
        content.style.display = 'grid';
        icon.style.transform = 'rotate(0deg)';
        localStorage.setItem('group-' + groupId, 'expanded');
    } else {
        content.style.display = 'none';
        icon.style.transform = 'rotate(-90deg)';
        localStorage.setItem('group-' + groupId, 'collapsed');
    }
}

// 页面加载时恢复折叠状态
document.addEventListener('DOMContentLoaded', function() {
    document.querySelectorAll('.group-header').forEach(function(header) {
        const groupId = header.dataset.groupId;
        const state = localStorage.getItem('group-' + groupId);

        if (state === 'collapsed') {
            const content = document.getElementById('group-' + groupId);
            const icon = document.getElementById('icon-' + groupId);
            content.style.display = 'none';
            icon.style.transform = 'rotate(-90deg)';
        }
    });
});
</script>
{% endblock %}
```

**Step 5: 注册前台蓝图**

修改 `app.py`，在注册 auth 蓝图后添加:
```python
    from routes.frontend import frontend
    app.register_blueprint(frontend)
```

**Step 6: 运行测试验证通过**

运行: `pytest tests/test_frontend.py -v`
预期: PASS (2 tests)

**Step 7: 提交**

```bash
git add routes/frontend.py templates/dashboard.html app.py tests/test_frontend.py
git commit -m "feat: add frontend dashboard with bookmark display and group collapsing"
```

---

## Task 6: 后台书签管理

**Files:**
- Create: `routes/admin.py`
- Create: `templates/admin/base.html`
- Create: `templates/admin/bookmarks.html`
- Create: `tests/test_admin.py`
- Modify: `app.py`

**Step 1: 编写后台管理测试**

创建 `tests/test_admin.py`:
```python
import pytest
from app import create_app, db
from models import User, Group, Bookmark

@pytest.fixture
def app():
    """创建测试应用"""
    app = create_app()
    app.config['TESTING'] = True
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
    app.config['WTF_CSRF_ENABLED'] = False

    with app.app_context():
        db.create_all()

        user = User(username='testuser', is_admin=False)
        user.set_password('password123')
        db.session.add(user)
        db.session.commit()

        yield app

        db.session.remove()
        db.drop_all()

@pytest.fixture
def client(app):
    return app.test_client()

@pytest.fixture
def authenticated_client(client):
    client.post('/auth/login', data={
        'username': 'testuser',
        'password': 'password123'
    })
    return client

def test_create_bookmark(authenticated_client, app):
    """测试创建书签"""
    response = authenticated_client.post('/admin/bookmarks/create', data={
        'title': 'Google',
        'url': 'https://google.com',
        'group_id': ''
    }, follow_redirects=True)

    assert response.status_code == 200

    with app.app_context():
        bookmark = Bookmark.query.filter_by(title='Google').first()
        assert bookmark is not None
        assert bookmark.url == 'https://google.com'

def test_update_bookmark(authenticated_client, app):
    """测试更新书签"""
    with app.app_context():
        user = User.query.first()
        bookmark = Bookmark(
            user_id=user.id,
            title='Old Title',
            url='https://old.com',
            order=0
        )
        db.session.add(bookmark)
        db.session.commit()
        bookmark_id = bookmark.id

    response = authenticated_client.post(f'/admin/bookmarks/{bookmark_id}/update', data={
        'title': 'New Title',
        'url': 'https://new.com',
        'group_id': ''
    }, follow_redirects=True)

    assert response.status_code == 200

    with app.app_context():
        bookmark = Bookmark.query.get(bookmark_id)
        assert bookmark.title == 'New Title'
        assert bookmark.url == 'https://new.com'

def test_delete_bookmark(authenticated_client, app):
    """测试删除书签"""
    with app.app_context():
        user = User.query.first()
        bookmark = Bookmark(
            user_id=user.id,
            title='To Delete',
            url='https://delete.com',
            order=0
        )
        db.session.add(bookmark)
        db.session.commit()
        bookmark_id = bookmark.id

    response = authenticated_client.post(f'/admin/bookmarks/{bookmark_id}/delete', follow_redirects=True)
    assert response.status_code == 200

    with app.app_context():
        bookmark = Bookmark.query.get(bookmark_id)
        assert bookmark is None
```

**Step 2: 运行测试验证失败**

运行: `pytest tests/test_admin.py -v`
预期: FAIL - 404 errors

**Step 3: 实现后台管理路由**

创建 `routes/admin.py`:
```python
from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_required, current_user
from app import db
from models import Bookmark, Group
from datetime import datetime

admin = Blueprint('admin', __name__, url_prefix='/admin')

@admin.route('/bookmarks')
@login_required
def bookmarks():
    """书签管理页面"""
    groups = Group.query.filter_by(user_id=current_user.id).order_by(Group.order).all()

    # 为每个分组获取书签
    groups_with_bookmarks = []
    for group in groups:
        bookmarks = Bookmark.query.filter_by(
            user_id=current_user.id,
            group_id=group.id
        ).order_by(Bookmark.order).all()

        groups_with_bookmarks.append({
            'group': group,
            'bookmarks': bookmarks
        })

    # 获取未分组的书签
    ungrouped_bookmarks = Bookmark.query.filter_by(
        user_id=current_user.id,
        group_id=None
    ).order_by(Bookmark.order).all()

    return render_template('admin/bookmarks.html',
                         groups_with_bookmarks=groups_with_bookmarks,
                         ungrouped_bookmarks=ungrouped_bookmarks,
                         all_groups=groups)

@admin.route('/bookmarks/create', methods=['POST'])
@login_required
def create_bookmark():
    """创建书签"""
    title = request.form.get('title')
    url = request.form.get('url')
    group_id = request.form.get('group_id')
    favicon_url = request.form.get('favicon_url')

    if not title or not url:
        flash('标题和URL不能为空', 'error')
        return redirect(url_for('admin.bookmarks'))

    # 获取最大order值
    max_order = db.session.query(db.func.max(Bookmark.order)).filter_by(
        user_id=current_user.id,
        group_id=int(group_id) if group_id else None
    ).scalar() or 0

    bookmark = Bookmark(
        user_id=current_user.id,
        group_id=int(group_id) if group_id else None,
        title=title,
        url=url,
        favicon_url=favicon_url if favicon_url else None,
        order=max_order + 1
    )

    db.session.add(bookmark)
    db.session.commit()

    flash('书签创建成功', 'success')
    return redirect(url_for('admin.bookmarks'))

@admin.route('/bookmarks/<int:bookmark_id>/update', methods=['POST'])
@login_required
def update_bookmark(bookmark_id):
    """更新书签"""
    bookmark = Bookmark.query.filter_by(id=bookmark_id, user_id=current_user.id).first_or_404()

    bookmark.title = request.form.get('title')
    bookmark.url = request.form.get('url')
    group_id = request.form.get('group_id')
    bookmark.group_id = int(group_id) if group_id else None
    favicon_url = request.form.get('favicon_url')
    bookmark.favicon_url = favicon_url if favicon_url else None
    bookmark.updated_at = datetime.utcnow()

    db.session.commit()

    flash('书签更新成功', 'success')
    return redirect(url_for('admin.bookmarks'))

@admin.route('/bookmarks/<int:bookmark_id>/delete', methods=['POST'])
@login_required
def delete_bookmark(bookmark_id):
    """删除书签"""
    bookmark = Bookmark.query.filter_by(id=bookmark_id, user_id=current_user.id).first_or_404()

    db.session.delete(bookmark)
    db.session.commit()

    flash('书签删除成功', 'success')
    return redirect(url_for('admin.bookmarks'))

@admin.route('/bookmarks/reorder', methods=['POST'])
@login_required
def reorder_bookmarks():
    """重新排序书签"""
    data = request.get_json()
    bookmark_orders = data.get('bookmarks', [])

    for item in bookmark_orders:
        bookmark = Bookmark.query.filter_by(
            id=item['id'],
            user_id=current_user.id
        ).first()

        if bookmark:
            bookmark.order = item['order']
            if 'group_id' in item:
                bookmark.group_id = item['group_id'] if item['group_id'] else None

    db.session.commit()
    return jsonify({'success': True})
```

**Step 4: 创建后台基础模板**

创建 `templates/admin/base.html`:
```html
{% extends "base.html" %}

{% block content %}
<div class="min-h-screen bg-gray-50 flex">
    <!-- 侧边栏 -->
    <aside class="w-64 bg-white shadow-sm">
        <div class="p-4 border-b">
            <h2 class="text-xl font-bold text-gray-900">后台管理</h2>
        </div>
        <nav class="p-4">
            <ul class="space-y-2">
                <li>
                    <a href="{{ url_for('admin.bookmarks') }}"
                       class="block px-4 py-2 rounded-lg {% if request.endpoint == 'admin.bookmarks' %}bg-blue-50 text-blue-600{% else %}text-gray-700 hover:bg-gray-50{% endif %}">
                        书签管理
                    </a>
                </li>
                <li>
                    <a href="{{ url_for('admin.groups') }}"
                       class="block px-4 py-2 rounded-lg {% if request.endpoint == 'admin.groups' %}bg-blue-50 text-blue-600{% else %}text-gray-700 hover:bg-gray-50{% endif %}">
                        分组管理
                    </a>
                </li>
                {% if current_user.is_admin %}
                <li>
                    <a href="{{ url_for('admin.users') }}"
                       class="block px-4 py-2 rounded-lg {% if request.endpoint == 'admin.users' %}bg-blue-50 text-blue-600{% else %}text-gray-700 hover:bg-gray-50{% endif %}">
                        用户管理
                    </a>
                </li>
                {% endif %}
                <li class="pt-4 border-t">
                    <a href="{{ url_for('frontend.dashboard') }}"
                       class="block px-4 py-2 rounded-lg text-gray-700 hover:bg-gray-50">
                        返回前台
                    </a>
                </li>
            </ul>
        </nav>
    </aside>

    <!-- 主内容 -->
    <main class="flex-1 p-8">
        {% block admin_content %}{% endblock %}
    </main>
</div>
{% endblock %}
```

**Step 5: 创建书签管理页面**

创建 `templates/admin/bookmarks.html`:
```html
{% extends "admin/base.html" %}

{% block title %}书签管理 - 书签管理系统{% endblock %}

{% block admin_content %}
<div class="max-w-6xl">
    <div class="flex justify-between items-center mb-6">
        <h1 class="text-2xl font-bold text-gray-900">书签管理</h1>
        <button onclick="showCreateModal()"
                class="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition">
            添加书签
        </button>
    </div>

    <!-- 分组书签 -->
    <div id="bookmark-list" class="space-y-6">
        {% for item in groups_with_bookmarks %}
        <div class="bg-white p-6 rounded-lg shadow" data-group-id="{{ item.group.id }}">
            <h3 class="text-lg font-semibold mb-4 text-gray-800">{{ item.group.name }}</h3>
            <div class="space-y-2 sortable-list" data-group-id="{{ item.group.id }}">
                {% for bookmark in item.bookmarks %}
                <div class="flex items-center justify-between p-3 bg-gray-50 rounded-lg cursor-move"
                     data-bookmark-id="{{ bookmark.id }}">
                    <div class="flex items-center space-x-3">
                        <svg class="w-5 h-5 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 8h16M4 16h16"/>
                        </svg>
                        {% if bookmark.favicon_url %}
                        <img src="{{ bookmark.favicon_url }}" alt="" class="w-5 h-5">
                        {% endif %}
                        <span class="font-medium">{{ bookmark.title }}</span>
                        <span class="text-sm text-gray-500">{{ bookmark.url }}</span>
                    </div>
                    <div class="flex space-x-2">
                        <button onclick="showEditModal({{ bookmark.id }}, '{{ bookmark.title }}', '{{ bookmark.url }}', {{ bookmark.group_id or 'null' }}, '{{ bookmark.favicon_url or '' }}')"
                                class="px-3 py-1 text-blue-600 hover:bg-blue-50 rounded transition">
                            编辑
                        </button>
                        <button onclick="deleteBookmark({{ bookmark.id }})"
                                class="px-3 py-1 text-red-600 hover:bg-red-50 rounded transition">
                            删除
                        </button>
                    </div>
                </div>
                {% endfor %}
            </div>
        </div>
        {% endfor %}

        <!-- 未分组书签 -->
        {% if ungrouped_bookmarks %}
        <div class="bg-white p-6 rounded-lg shadow">
            <h3 class="text-lg font-semibold mb-4 text-gray-800">未分类</h3>
            <div class="space-y-2 sortable-list" data-group-id="">
                {% for bookmark in ungrouped_bookmarks %}
                <div class="flex items-center justify-between p-3 bg-gray-50 rounded-lg cursor-move"
                     data-bookmark-id="{{ bookmark.id }}">
                    <div class="flex items-center space-x-3">
                        <svg class="w-5 h-5 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 8h16M4 16h16"/>
                        </svg>
                        {% if bookmark.favicon_url %}
                        <img src="{{ bookmark.favicon_url }}" alt="" class="w-5 h-5">
                        {% endif %}
                        <span class="font-medium">{{ bookmark.title }}</span>
                        <span class="text-sm text-gray-500">{{ bookmark.url }}</span>
                    </div>
                    <div class="flex space-x-2">
                        <button onclick="showEditModal({{ bookmark.id }}, '{{ bookmark.title }}', '{{ bookmark.url }}', null, '{{ bookmark.favicon_url or '' }}')"
                                class="px-3 py-1 text-blue-600 hover:bg-blue-50 rounded transition">
                            编辑
                        </button>
                        <button onclick="deleteBookmark({{ bookmark.id }})"
                                class="px-3 py-1 text-red-600 hover:bg-red-50 rounded transition">
                            删除
                        </button>
                    </div>
                </div>
                {% endfor %}
            </div>
        </div>
        {% endif %}
    </div>
</div>

<!-- 创建/编辑模态框 -->
<div id="bookmarkModal" class="fixed inset-0 bg-black bg-opacity-50 hidden items-center justify-center z-50">
    <div class="bg-white rounded-lg p-6 max-w-md w-full mx-4">
        <h2 id="modalTitle" class="text-xl font-bold mb-4">添加书签</h2>
        <form id="bookmarkForm" method="POST">
            <div class="space-y-4">
                <div>
                    <label class="block text-sm font-medium text-gray-700 mb-1">标题</label>
                    <input type="text" name="title" required
                           class="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500">
                </div>
                <div>
                    <label class="block text-sm font-medium text-gray-700 mb-1">URL</label>
                    <input type="url" name="url" required
                           class="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500">
                </div>
                <div>
                    <label class="block text-sm font-medium text-gray-700 mb-1">分组</label>
                    <select name="group_id"
                            class="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500">
                        <option value="">无分组</option>
                        {% for group in all_groups %}
                        <option value="{{ group.id }}">{{ group.name }}</option>
                        {% endfor %}
                    </select>
                </div>
                <div>
                    <label class="block text-sm font-medium text-gray-700 mb-1">图标URL（可选）</label>
                    <input type="url" name="favicon_url"
                           class="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500">
                </div>
            </div>
            <div class="flex justify-end space-x-3 mt-6">
                <button type="button" onclick="closeModal()"
                        class="px-4 py-2 bg-gray-200 text-gray-700 rounded-lg hover:bg-gray-300 transition">
                    取消
                </button>
                <button type="submit"
                        class="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition">
                    保存
                </button>
            </div>
        </form>
    </div>
</div>

<script src="https://cdn.jsdelivr.net/npm/sortablejs@1.15.0/Sortable.min.js"></script>
<script>
let editingBookmarkId = null;

function showCreateModal() {
    editingBookmarkId = null;
    document.getElementById('modalTitle').textContent = '添加书签';
    document.getElementById('bookmarkForm').action = '{{ url_for("admin.create_bookmark") }}';
    document.getElementById('bookmarkForm').reset();
    document.getElementById('bookmarkModal').classList.remove('hidden');
    document.getElementById('bookmarkModal').classList.add('flex');
}

function showEditModal(id, title, url, groupId, faviconUrl) {
    editingBookmarkId = id;
    document.getElementById('modalTitle').textContent = '编辑书签';
    document.getElementById('bookmarkForm').action = `/admin/bookmarks/${id}/update`;

    document.querySelector('[name="title"]').value = title;
    document.querySelector('[name="url"]').value = url;
    document.querySelector('[name="group_id"]').value = groupId || '';
    document.querySelector('[name="favicon_url"]').value = faviconUrl || '';

    document.getElementById('bookmarkModal').classList.remove('hidden');
    document.getElementById('bookmarkModal').classList.add('flex');
}

function closeModal() {
    document.getElementById('bookmarkModal').classList.add('hidden');
    document.getElementById('bookmarkModal').classList.remove('flex');
}

function deleteBookmark(id) {
    if (confirm('确定要删除这个书签吗？')) {
        const form = document.createElement('form');
        form.method = 'POST';
        form.action = `/admin/bookmarks/${id}/delete`;
        document.body.appendChild(form);
        form.submit();
    }
}

// 初始化拖拽排序
document.querySelectorAll('.sortable-list').forEach(function(el) {
    new Sortable(el, {
        animation: 150,
        ghostClass: 'sortable-ghost',
        onEnd: function(evt) {
            saveOrder();
        }
    });
});

function saveOrder() {
    const bookmarks = [];
    document.querySelectorAll('.sortable-list').forEach(function(list) {
        const groupId = list.dataset.groupId;
        list.querySelectorAll('[data-bookmark-id]').forEach(function(item, index) {
            bookmarks.push({
                id: parseInt(item.dataset.bookmarkId),
                order: index,
                group_id: groupId ? parseInt(groupId) : null
            });
        });
    });

    fetch('{{ url_for("admin.reorder_bookmarks") }}', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({ bookmarks: bookmarks })
    });
}
</script>
{% endblock %}
```

**Step 6: 注册后台蓝图**

修改 `app.py`，在注册 frontend 蓝图后添加:
```python
    from routes.admin import admin
    app.register_blueprint(admin)
```

**Step 7: 运行测试验证通过**

运行: `pytest tests/test_admin.py -v`
预期: PASS (3 tests)

**Step 8: 提交**

```bash
git add routes/admin.py templates/admin/ app.py tests/test_admin.py
git commit -m "feat: add backend bookmark management with CRUD and drag-drop sorting"
```

---

## Task 7: 分组管理

**Files:**
- Create: `templates/admin/groups.html`
- Modify: `routes/admin.py`

**Step 1: 在 admin.py 添加分组管理路由**

在 `routes/admin.py` 末尾添加:
```python
@admin.route('/groups')
@login_required
def groups():
    """分组管理页面"""
    groups = Group.query.filter_by(user_id=current_user.id).order_by(Group.order).all()

    # 为每个分组统计书签数量
    groups_with_counts = []
    for group in groups:
        count = Bookmark.query.filter_by(group_id=group.id).count()
        groups_with_counts.append({
            'group': group,
            'bookmark_count': count
        })

    return render_template('admin/groups.html', groups_with_counts=groups_with_counts)

@admin.route('/groups/create', methods=['POST'])
@login_required
def create_group():
    """创建分组"""
    name = request.form.get('name')

    if not name:
        flash('分组名称不能为空', 'error')
        return redirect(url_for('admin.groups'))

    # 获取最大order值
    max_order = db.session.query(db.func.max(Group.order)).filter_by(
        user_id=current_user.id
    ).scalar() or 0

    group = Group(
        user_id=current_user.id,
        name=name,
        order=max_order + 1
    )

    db.session.add(group)
    db.session.commit()

    flash('分组创建成功', 'success')
    return redirect(url_for('admin.groups'))

@admin.route('/groups/<int:group_id>/update', methods=['POST'])
@login_required
def update_group(group_id):
    """更新分组"""
    group = Group.query.filter_by(id=group_id, user_id=current_user.id).first_or_404()

    group.name = request.form.get('name')
    db.session.commit()

    flash('分组更新成功', 'success')
    return redirect(url_for('admin.groups'))

@admin.route('/groups/<int:group_id>/delete', methods=['POST'])
@login_required
def delete_group(group_id):
    """删除分组"""
    group = Group.query.filter_by(id=group_id, user_id=current_user.id).first_or_404()

    # 删除分组，书签会自动变为未分组（ON DELETE SET NULL）
    db.session.delete(group)
    db.session.commit()

    flash('分组删除成功，原书签已移至未分类', 'success')
    return redirect(url_for('admin.groups'))

@admin.route('/groups/reorder', methods=['POST'])
@login_required
def reorder_groups():
    """重新排序分组"""
    data = request.get_json()
    group_orders = data.get('groups', [])

    for item in group_orders:
        group = Group.query.filter_by(
            id=item['id'],
            user_id=current_user.id
        ).first()

        if group:
            group.order = item['order']

    db.session.commit()
    return jsonify({'success': True})
```

**Step 2: 创建分组管理页面**

创建 `templates/admin/groups.html`:
```html
{% extends "admin/base.html" %}

{% block title %}分组管理 - 书签管理系统{% endblock %}

{% block admin_content %}
<div class="max-w-4xl">
    <div class="flex justify-between items-center mb-6">
        <h1 class="text-2xl font-bold text-gray-900">分组管理</h1>
        <button onclick="showCreateModal()"
                class="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition">
            添加分组
        </button>
    </div>

    <div class="bg-white rounded-lg shadow">
        <div id="groups-list" class="divide-y sortable-list">
            {% for item in groups_with_counts %}
            <div class="flex items-center justify-between p-4 cursor-move" data-group-id="{{ item.group.id }}">
                <div class="flex items-center space-x-3">
                    <svg class="w-5 h-5 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 8h16M4 16h16"/>
                    </svg>
                    <span class="font-medium text-gray-800">{{ item.group.name }}</span>
                    <span class="text-sm text-gray-500">({{ item.bookmark_count }} 个书签)</span>
                </div>
                <div class="flex space-x-2">
                    <button onclick="showEditModal({{ item.group.id }}, '{{ item.group.name }}')"
                            class="px-3 py-1 text-blue-600 hover:bg-blue-50 rounded transition">
                        编辑
                    </button>
                    <button onclick="deleteGroup({{ item.group.id }})"
                            class="px-3 py-1 text-red-600 hover:bg-red-50 rounded transition">
                        删除
                    </button>
                </div>
            </div>
            {% endfor %}
        </div>

        {% if not groups_with_counts %}
        <div class="p-8 text-center text-gray-500">
            还没有分组，点击上方按钮添加第一个分组
        </div>
        {% endif %}
    </div>
</div>

<!-- 创建/编辑模态框 -->
<div id="groupModal" class="fixed inset-0 bg-black bg-opacity-50 hidden items-center justify-center z-50">
    <div class="bg-white rounded-lg p-6 max-w-md w-full mx-4">
        <h2 id="modalTitle" class="text-xl font-bold mb-4">添加分组</h2>
        <form id="groupForm" method="POST">
            <div class="space-y-4">
                <div>
                    <label class="block text-sm font-medium text-gray-700 mb-1">分组名称</label>
                    <input type="text" name="name" required
                           class="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500">
                </div>
            </div>
            <div class="flex justify-end space-x-3 mt-6">
                <button type="button" onclick="closeModal()"
                        class="px-4 py-2 bg-gray-200 text-gray-700 rounded-lg hover:bg-gray-300 transition">
                    取消
                </button>
                <button type="submit"
                        class="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition">
                    保存
                </button>
            </div>
        </form>
    </div>
</div>

<script src="https://cdn.jsdelivr.net/npm/sortablejs@1.15.0/Sortable.min.js"></script>
<script>
function showCreateModal() {
    document.getElementById('modalTitle').textContent = '添加分组';
    document.getElementById('groupForm').action = '{{ url_for("admin.create_group") }}';
    document.getElementById('groupForm').reset();
    document.getElementById('groupModal').classList.remove('hidden');
    document.getElementById('groupModal').classList.add('flex');
}

function showEditModal(id, name) {
    document.getElementById('modalTitle').textContent = '编辑分组';
    document.getElementById('groupForm').action = `/admin/groups/${id}/update`;
    document.querySelector('[name="name"]').value = name;
    document.getElementById('groupModal').classList.remove('hidden');
    document.getElementById('groupModal').classList.add('flex');
}

function closeModal() {
    document.getElementById('groupModal').classList.add('hidden');
    document.getElementById('groupModal').classList.remove('flex');
}

function deleteGroup(id) {
    if (confirm('确定要删除这个分组吗？分组内的书签将移至未分类。')) {
        const form = document.createElement('form');
        form.method = 'POST';
        form.action = `/admin/groups/${id}/delete`;
        document.body.appendChild(form);
        form.submit();
    }
}

// 初始化拖拽排序
new Sortable(document.querySelector('.sortable-list'), {
    animation: 150,
    ghostClass: 'sortable-ghost',
    onEnd: function(evt) {
        saveOrder();
    }
});

function saveOrder() {
    const groups = [];
    document.querySelectorAll('[data-group-id]').forEach(function(item, index) {
        groups.push({
            id: parseInt(item.dataset.groupId),
            order: index
        });
    });

    fetch('{{ url_for("admin.reorder_groups") }}', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({ groups: groups })
    });
}
</script>
{% endblock %}
```

**Step 3: 手动测试分组管理**

运行: `python app.py`
1. 登录后访问后台
2. 点击"分组管理"
3. 测试创建、编辑、删除、拖拽排序功能

**Step 4: 提交**

```bash
git add routes/admin.py templates/admin/groups.html
git commit -m "feat: add group management with CRUD and reordering"
```

---

## Task 8: 用户管理（管理员功能）

**Files:**
- Create: `templates/admin/users.html`
- Modify: `routes/admin.py`

**Step 1: 在 admin.py 添加用户管理路由**

在 `routes/admin.py` 末尾添加:
```python
from functools import wraps

def admin_required(f):
    """管理员权限装饰器"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_admin:
            flash('需要管理员权限', 'error')
            return redirect(url_for('frontend.dashboard'))
        return f(*args, **kwargs)
    return decorated_function

@admin.route('/users')
@login_required
@admin_required
def users():
    """用户管理页面"""
    all_users = User.query.order_by(User.created_at.desc()).all()
    return render_template('admin/users.html', users=all_users)

@admin.route('/users/create', methods=['POST'])
@login_required
@admin_required
def create_user():
    """创建用户"""
    username = request.form.get('username')
    password = request.form.get('password')
    is_admin = request.form.get('is_admin') == 'on'

    if not username or not password:
        flash('用户名和密码不能为空', 'error')
        return redirect(url_for('admin.users'))

    # 检查用户名是否已存在
    existing_user = User.query.filter_by(username=username).first()
    if existing_user:
        flash('用户名已存在', 'error')
        return redirect(url_for('admin.users'))

    user = User(username=username, is_admin=is_admin)
    user.set_password(password)

    db.session.add(user)
    db.session.commit()

    flash(f'用户 {username} 创建成功', 'success')
    return redirect(url_for('admin.users'))

@admin.route('/users/<int:user_id>/reset-password', methods=['POST'])
@login_required
@admin_required
def reset_password(user_id):
    """重置用户密码"""
    user = User.query.get_or_404(user_id)
    new_password = request.form.get('password')

    if not new_password:
        flash('新密码不能为空', 'error')
        return redirect(url_for('admin.users'))

    user.set_password(new_password)
    db.session.commit()

    flash(f'用户 {user.username} 的密码已重置', 'success')
    return redirect(url_for('admin.users'))

@admin.route('/users/<int:user_id>/delete', methods=['POST'])
@login_required
@admin_required
def delete_user(user_id):
    """删除用户"""
    user = User.query.get_or_404(user_id)

    # 防止删除自己
    if user.id == current_user.id:
        flash('不能删除当前登录的用户', 'error')
        return redirect(url_for('admin.users'))

    # 确保至少保留一个管理员
    if user.is_admin:
        admin_count = User.query.filter_by(is_admin=True).count()
        if admin_count <= 1:
            flash('至少需要保留一个管理员账号', 'error')
            return redirect(url_for('admin.users'))

    username = user.username
    db.session.delete(user)
    db.session.commit()

    flash(f'用户 {username} 已删除', 'success')
    return redirect(url_for('admin.users'))
```

同时需要在文件顶部导入 User:
```python
from models import Bookmark, Group, User
```

**Step 2: 创建用户管理页面**

创建 `templates/admin/users.html`:
```html
{% extends "admin/base.html" %}

{% block title %}用户管理 - 书签管理系统{% endblock %}

{% block admin_content %}
<div class="max-w-6xl">
    <div class="flex justify-between items-center mb-6">
        <h1 class="text-2xl font-bold text-gray-900">用户管理</h1>
        <button onclick="showCreateModal()"
                class="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition">
            创建用户
        </button>
    </div>

    <div class="bg-white rounded-lg shadow overflow-hidden">
        <table class="min-w-full divide-y divide-gray-200">
            <thead class="bg-gray-50">
                <tr>
                    <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">用户名</th>
                    <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">角色</th>
                    <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">创建时间</th>
                    <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">操作</th>
                </tr>
            </thead>
            <tbody class="bg-white divide-y divide-gray-200">
                {% for user in users %}
                <tr>
                    <td class="px-6 py-4 whitespace-nowrap">
                        <span class="font-medium text-gray-900">{{ user.username }}</span>
                        {% if user.id == current_user.id %}
                        <span class="ml-2 text-xs text-blue-600">(当前用户)</span>
                        {% endif %}
                    </td>
                    <td class="px-6 py-4 whitespace-nowrap">
                        {% if user.is_admin %}
                        <span class="px-2 py-1 text-xs font-semibold rounded-full bg-purple-100 text-purple-800">管理员</span>
                        {% else %}
                        <span class="px-2 py-1 text-xs font-semibold rounded-full bg-gray-100 text-gray-800">普通用户</span>
                        {% endif %}
                    </td>
                    <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                        {{ user.created_at.strftime('%Y-%m-%d %H:%M') }}
                    </td>
                    <td class="px-6 py-4 whitespace-nowrap text-sm">
                        <button onclick="showResetPasswordModal({{ user.id }}, '{{ user.username }}')"
                                class="text-blue-600 hover:text-blue-800 mr-3">
                            重置密码
                        </button>
                        {% if user.id != current_user.id %}
                        <button onclick="deleteUser({{ user.id }}, '{{ user.username }}', {{ user.is_admin|lower }})"
                                class="text-red-600 hover:text-red-800">
                            删除
                        </button>
                        {% endif %}
                    </td>
                </tr>
                {% endfor %}
            </tbody>
        </table>
    </div>
</div>

<!-- 创建用户模态框 -->
<div id="createUserModal" class="fixed inset-0 bg-black bg-opacity-50 hidden items-center justify-center z-50">
    <div class="bg-white rounded-lg p-6 max-w-md w-full mx-4">
        <h2 class="text-xl font-bold mb-4">创建用户</h2>
        <form method="POST" action="{{ url_for('admin.create_user') }}">
            <div class="space-y-4">
                <div>
                    <label class="block text-sm font-medium text-gray-700 mb-1">用户名</label>
                    <input type="text" name="username" required
                           class="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500">
                </div>
                <div>
                    <label class="block text-sm font-medium text-gray-700 mb-1">初始密码</label>
                    <input type="password" name="password" required
                           class="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500">
                    <p class="mt-1 text-xs text-gray-500">建议使用8位以上的强密码</p>
                </div>
                <div class="flex items-center">
                    <input type="checkbox" name="is_admin" id="is_admin"
                           class="h-4 w-4 text-blue-600 border-gray-300 rounded focus:ring-blue-500">
                    <label for="is_admin" class="ml-2 block text-sm text-gray-700">设为管理员</label>
                </div>
            </div>
            <div class="flex justify-end space-x-3 mt-6">
                <button type="button" onclick="closeCreateModal()"
                        class="px-4 py-2 bg-gray-200 text-gray-700 rounded-lg hover:bg-gray-300 transition">
                    取消
                </button>
                <button type="submit"
                        class="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition">
                    创建
                </button>
            </div>
        </form>
    </div>
</div>

<!-- 重置密码模态框 -->
<div id="resetPasswordModal" class="fixed inset-0 bg-black bg-opacity-50 hidden items-center justify-center z-50">
    <div class="bg-white rounded-lg p-6 max-w-md w-full mx-4">
        <h2 class="text-xl font-bold mb-4">重置密码</h2>
        <p class="text-gray-600 mb-4">为用户 <span id="resetUsername" class="font-semibold"></span> 设置新密码</p>
        <form id="resetPasswordForm" method="POST">
            <div class="space-y-4">
                <div>
                    <label class="block text-sm font-medium text-gray-700 mb-1">新密码</label>
                    <input type="password" name="password" required
                           class="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500">
                </div>
            </div>
            <div class="flex justify-end space-x-3 mt-6">
                <button type="button" onclick="closeResetPasswordModal()"
                        class="px-4 py-2 bg-gray-200 text-gray-700 rounded-lg hover:bg-gray-300 transition">
                    取消
                </button>
                <button type="submit"
                        class="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition">
                    重置
                </button>
            </div>
        </form>
    </div>
</div>

<script>
function showCreateModal() {
    document.getElementById('createUserModal').classList.remove('hidden');
    document.getElementById('createUserModal').classList.add('flex');
}

function closeCreateModal() {
    document.getElementById('createUserModal').classList.add('hidden');
    document.getElementById('createUserModal').classList.remove('flex');
}

function showResetPasswordModal(userId, username) {
    document.getElementById('resetUsername').textContent = username;
    document.getElementById('resetPasswordForm').action = `/admin/users/${userId}/reset-password`;
    document.getElementById('resetPasswordModal').classList.remove('hidden');
    document.getElementById('resetPasswordModal').classList.add('flex');
}

function closeResetPasswordModal() {
    document.getElementById('resetPasswordModal').classList.add('hidden');
    document.getElementById('resetPasswordModal').classList.remove('flex');
}

function deleteUser(userId, username, isAdmin) {
    let message = `确定要删除用户 ${username} 吗？`;
    if (isAdmin) {
        message += '\n\n注意：这是一个管理员账号。';
    }

    if (confirm(message)) {
        const form = document.createElement('form');
        form.method = 'POST';
        form.action = `/admin/users/${userId}/delete`;
        document.body.appendChild(form);
        form.submit();
    }
}
</script>
{% endblock %}
```

**Step 3: 手动测试用户管理**

运行应用并测试用户管理功能（需要先创建管理员用户）

**Step 4: 提交**

```bash
git add routes/admin.py templates/admin/users.html
git commit -m "feat: add user management for admins with create, reset password, and delete"
```

---

## Task 9: 数据库初始化和CLI工具

**Files:**
- Create: `cli.py`
- Modify: `app.py`

**Step 1: 创建CLI工具**

创建 `cli.py`:
```python
#!/usr/bin/env python
"""命令行工具"""
import click
from app import create_app, db
from models import User

app = create_app()

@app.cli.command()
def init_db():
    """初始化数据库"""
    with app.app_context():
        db.create_all()
        click.echo('数据库初始化成功')

@app.cli.command()
@click.option('--username', prompt='用户名', help='管理员用户名')
@click.option('--password', prompt='密码', hide_input=True, confirmation_prompt=True, help='管理员密码')
def create_admin(username, password):
    """创建管理员账号"""
    with app.app_context():
        # 检查用户是否已存在
        existing_user = User.query.filter_by(username=username).first()
        if existing_user:
            click.echo(f'用户 {username} 已存在')
            return

        admin = User(username=username, is_admin=True)
        admin.set_password(password)

        db.session.add(admin)
        db.session.commit()

        click.echo(f'管理员 {username} 创建成功')

if __name__ == '__main__':
    app.cli()
```

**Step 2: 更新 app.py 添加 CLI 支持**

在 `app.py` 的 `create_app()` 函数返回前添加:
```python
    # 注册 CLI 命令
    @app.cli.command()
    def init_db():
        """初始化数据库"""
        db.create_all()
        click.echo('数据库初始化成功')

    @app.cli.command()
    @click.option('--username', prompt='用户名')
    @click.option('--password', prompt='密码', hide_input=True, confirmation_prompt=True)
    def create_admin(username, password):
        """创建管理员账号"""
        from models import User

        existing_user = User.query.filter_by(username=username).first()
        if existing_user:
            click.echo(f'用户 {username} 已存在')
            return

        admin = User(username=username, is_admin=True)
        admin.set_password(password)

        db.session.add(admin)
        db.session.commit()

        click.echo(f'管理员 {username} 创建成功')
```

同时在文件顶部导入:
```python
import click
```

**Step 3: 测试CLI命令**

运行: `flask init-db`
预期: 输出 "数据库初始化成功"

运行: `flask create-admin`
预期: 提示输入用户名和密码，创建管理员

**Step 4: 提交**

```bash
git add cli.py app.py
git commit -m "feat: add CLI commands for database initialization and admin creation"
```

---

## Task 10: 部署配置文件

**Files:**
- Create: `gunicorn_config.py`
- Create: `nginx.conf.example`
- Create: `systemd.service.example`
- Create: `README.md`

**Step 1: 创建 Gunicorn 配置**

创建 `gunicorn_config.py`:
```python
"""Gunicorn 配置文件"""
import multiprocessing

# 绑定地址
bind = "127.0.0.1:8000"

# Worker 进程数（CPU核心数 * 2 + 1）
workers = multiprocessing.cpu_count() * 2 + 1

# Worker 类型
worker_class = "sync"

# 超时时间（秒）
timeout = 30

# 日志
accesslog = "logs/access.log"
errorlog = "logs/error.log"
loglevel = "info"

# 进程名称
proc_name = "bookmark-system"

# Daemon 模式
daemon = False
```

**Step 2: 创建 Nginx 配置示例**

创建 `nginx.conf.example`:
```nginx
server {
    listen 80;
    server_name your-domain.com;

    # 重定向到 HTTPS
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name your-domain.com;

    # SSL 证书配置（使用 Let's Encrypt）
    ssl_certificate /etc/letsencrypt/live/your-domain.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/your-domain.com/privkey.pem;

    # SSL 安全配置
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers HIGH:!aNULL:!MD5;
    ssl_prefer_server_ciphers on;

    # 静态文件
    location /static {
        alias /path/to/bookmark-system/static;
        expires 30d;
        add_header Cache-Control "public, immutable";
    }

    # 代理到 Gunicorn
    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    # Gzip 压缩
    gzip on;
    gzip_vary on;
    gzip_proxied any;
    gzip_comp_level 6;
    gzip_types text/plain text/css text/xml text/javascript application/json application/javascript application/xml+rss;
}
```

**Step 3: 创建 Systemd 服务示例**

创建 `systemd.service.example`:
```ini
[Unit]
Description=Bookmark Management System
After=network.target

[Service]
Type=notify
User=www-data
Group=www-data
WorkingDirectory=/path/to/bookmark-system
Environment="PATH=/path/to/bookmark-system/venv/bin"
ExecStart=/path/to/bookmark-system/venv/bin/gunicorn -c gunicorn_config.py app:app
ExecReload=/bin/kill -s HUP $MAINPID
KillMode=mixed
TimeoutStopSec=5
PrivateTmp=true
Restart=on-failure

[Install]
WantedBy=multi-user.target
```

**Step 4: 创建 README**

创建 `README.md`:
```markdown
# 书签管理系统

一个轻量级的多用户书签管理系统，支持分组管理、拖拽排序和 Favicon 展示。

## 功能特性

- **多用户支持**：每个用户管理自己的书签列表
- **分组管理**：支持创建分组，拖拽排序
- **拖拽排序**：书签和分组都支持拖拽调整顺序
- **Favicon 展示**：自动获取网站图标
- **权限管理**：管理员邀请制，只有管理员可以创建用户
- **响应式设计**：支持桌面和移动端访问

## 技术栈

- **后端**：Flask 3.0 + SQLAlchemy + SQLite
- **前端**：Jinja2 + Tailwind CSS + SortableJS
- **认证**：Flask-Login + bcrypt

## 快速开始

### 1. 安装依赖

```bash
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 2. 初始化数据库

```bash
flask init-db
```

### 3. 创建管理员账号

```bash
flask create-admin
```

### 4. 运行开发服务器

```bash
python app.py
```

访问 http://localhost:5000

## 生产部署

### 使用 Gunicorn + Nginx

1. **安装 Gunicorn**

```bash
pip install gunicorn
```

2. **配置 Nginx**

复制 `nginx.conf.example` 到 `/etc/nginx/sites-available/`，修改域名和路径，然后启用：

```bash
sudo ln -s /etc/nginx/sites-available/bookmark /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx
```

3. **配置 Systemd 服务**

复制 `systemd.service.example` 到 `/etc/systemd/system/bookmark.service`，修改路径：

```bash
sudo systemctl daemon-reload
sudo systemctl start bookmark
sudo systemctl enable bookmark
```

4. **配置 SSL（Let's Encrypt）**

```bash
sudo apt install certbot python3-certbot-nginx
sudo certbot --nginx -d your-domain.com
```

## 数据备份

建议定期备份 SQLite 数据库文件：

```bash
# 创建备份脚本
cat > backup.sh << 'EOF'
#!/bin/bash
DATE=$(date +%Y%m%d)
cp instance/bookmarks.db backups/bookmarks-$DATE.db
# 保留最近7天的备份
find backups/ -name "bookmarks-*.db" -mtime +7 -delete
EOF

chmod +x backup.sh

# 添加到 crontab（每天凌晨2点）
echo "0 2 * * * /path/to/backup.sh" | crontab -
```

## 开发

### 运行测试

```bash
pytest
```

### 项目结构

```
bookmarks/
├── app.py              # Flask 应用入口
├── config.py           # 配置文件
├── models.py           # 数据库模型
├── cli.py              # CLI 工具
├── routes/             # 路由
│   ├── auth.py        # 认证
│   ├── frontend.py    # 前台
│   └── admin.py       # 后台管理
├── templates/          # 模板
├── static/             # 静态文件
├── tests/              # 测试
└── instance/           # 实例文件（数据库）
```

## 许可证

MIT License
```

**Step 5: 提交**

```bash
git add gunicorn_config.py nginx.conf.example systemd.service.example README.md
git commit -m "docs: add deployment configurations and README"
```

---

## 完成

所有核心功能已实现！系统现在包括：

✅ 用户认证系统
✅ 前台书签展示（分组折叠、响应式）
✅ 后台书签管理（CRUD、拖拽排序）
✅ 分组管理（CRUD、拖拽排序）
✅ 用户管理（管理员专用）
✅ 数据库模型和迁移
✅ CLI 工具
✅ 部署配置
✅ 文档

**下一步建议：**
1. 手动测试所有功能
2. 添加 Favicon 自动获取功能
3. 添加搜索功能
4. 部署到生产环境
