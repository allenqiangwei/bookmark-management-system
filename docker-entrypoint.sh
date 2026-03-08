#!/bin/sh
set -e

# 确保 instance 目录存在
mkdir -p /app/instance/favicons

# 初始化数据库（如果还未创建表）
flask init-db

# 启动应用
exec gunicorn --bind 0.0.0.0:8000 --workers 2 --timeout 30 "app:create_app()"
