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
