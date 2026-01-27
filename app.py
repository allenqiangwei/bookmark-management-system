import os
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from dotenv import load_dotenv

load_dotenv()

from config import Config

db = SQLAlchemy()
login_manager = LoginManager()

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

    # 创建实例文件夹
    os.makedirs(os.path.join(app.instance_path), exist_ok=True)
    os.makedirs(os.path.join(app.instance_path, 'favicons'), exist_ok=True)

    return app

if __name__ == '__main__':
    app = create_app()
    app.run(debug=True)
