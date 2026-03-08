"""
CLI 命令模块
"""
import click
from app import db
from models import User

@click.command()
def init_db():
    """初始化数据库"""
    db.create_all()
    click.echo('数据库初始化成功')

@click.command()
@click.option('--username', prompt='用户名')
@click.option('--password', prompt='密码', hide_input=True, confirmation_prompt=True)
def create_admin(username, password):
    """创建管理员账号"""
    existing_user = User.query.filter_by(username=username).first()
    if existing_user:
        click.echo(f'用户 {username} 已存在')
        return

    admin = User(username=username, is_admin=True)
    admin.set_password(password)

    db.session.add(admin)
    db.session.commit()

    click.echo(f'管理员 {username} 创建成功')

def register_commands(app):
    """注册 CLI 命令到 Flask 应用"""
    app.cli.add_command(init_db)
    app.cli.add_command(create_admin)
