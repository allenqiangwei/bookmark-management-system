import os
import click
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_wtf.csrf import CSRFProtect
from dotenv import load_dotenv

load_dotenv()

from config import Config

db = SQLAlchemy()
login_manager = LoginManager()
csrf = CSRFProtect()

def create_app(config_overrides=None):
    """应用工厂函数"""
    app = Flask(__name__)
    app.config.from_object(Config)

    # 应用配置覆盖（用于测试）
    if config_overrides:
        app.config.update(config_overrides)

    # 初始化扩展
    db.init_app(app)
    login_manager.init_app(app)
    login_manager.login_view = 'auth.login'
    csrf.init_app(app)

    # 创建实例文件夹
    os.makedirs(os.path.join(app.instance_path), exist_ok=True)
    os.makedirs(os.path.join(app.instance_path, 'favicons'), exist_ok=True)

    # 注册蓝图
    from routes.auth import auth
    app.register_blueprint(auth)

    from routes.frontend import frontend
    app.register_blueprint(frontend)

    from routes.admin import admin
    app.register_blueprint(admin)

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

    return app

if __name__ == '__main__':
    app = create_app()
    app.run(debug=True)
