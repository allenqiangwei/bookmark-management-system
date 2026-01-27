# 网址管理系统设计文档

## 项目概述

一个轻量级的网址书签管理系统，支持多用户、分组管理、拖拽排序和 Favicon 展示。

### 目标用户
- 多用户系统，每个用户管理自己独立的网址列表
- 管理员邀请制，只有管理员可以创建新用户

### 核心功能
- **前台**：登录后展示个人网址列表，支持分组折叠和快速访问
- **后台**：管理网址（增删改查）、分组管理、拖拽排序
- **管理员**：用户管理（创建、删除、重置密码）

---

## 技术栈

- **后端**：Flask + Flask-Login + SQLAlchemy
- **前端**：Jinja2 模板 + Tailwind CSS + SortableJS
- **数据库**：SQLite
- **部署**：Gunicorn + Nginx

---

## 系统架构

```
用户浏览器
    ↓
Nginx (反向代理)
    ↓
Gunicorn (WSGI 服务器)
    ↓
Flask 应用
    ↓
SQLite 数据库
```

---

## 数据库设计

### users 表
```sql
CREATE TABLE users (
    id INTEGER PRIMARY KEY,
    username TEXT UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,
    is_admin BOOLEAN DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### groups 表
```sql
CREATE TABLE groups (
    id INTEGER PRIMARY KEY,
    user_id INTEGER NOT NULL,
    name TEXT NOT NULL,
    order INTEGER DEFAULT 0,
    is_collapsed BOOLEAN DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);
```

### bookmarks 表
```sql
CREATE TABLE bookmarks (
    id INTEGER PRIMARY KEY,
    user_id INTEGER NOT NULL,
    group_id INTEGER,
    title TEXT NOT NULL,
    url TEXT NOT NULL,
    favicon_url TEXT,
    order INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (group_id) REFERENCES groups(id) ON DELETE SET NULL
);
```

### 关系说明
- 一个用户可以有多个分组和多个书签
- 一个分组可以包含多个书签
- 书签可以不属于任何分组（group_id 为 NULL）
- 用户数据完全隔离

---

## 功能设计

### 1. 前台展示页面

#### 布局结构
- **顶部导航栏**：网站标题 + 用户名 + 退出 + 管理按钮
- **分组展示区**：可折叠的分组卡片
- **网址卡片**：大图标 + 名称，响应式网格布局
- **未分组书签**：显示在底部

#### 交互特性
- 分组折叠状态保存到 localStorage
- 点击卡片直接跳转到目标网址
- 悬停效果：阴影加深、轻微放大

### 2. 后台管理页面

#### 侧边栏导航
- 书签管理
- 分组管理
- 用户管理（仅管理员）
- 返回前台

#### 书签管理
- **列表视图**：按分组展示，支持拖拽排序
- **添加/编辑表单**：
  - 名称（必填）
  - URL（必填，格式验证）
  - 所属分组（下拉选择）
  - Favicon URL（自动获取，可手动覆盖）
- **拖拽排序**：
  - 分组内拖拽：调整书签顺序
  - 跨分组拖拽：移动书签到其他分组
  - 拖拽分组：调整分组顺序

#### 分组管理
- 列表展示：名称 + 书签数量 + 默认折叠状态
- 操作：编辑、删除（删除后书签变未分组）
- 支持拖拽调整分组顺序

### 3. 用户管理（管理员）

#### 登录系统
- 简洁的登录页面：用户名 + 密码
- "记住我"选项（30天会话）
- Flask-Login 管理会话
- 会话过期自动跳转登录页

#### 用户管理
- **用户列表**：用户名 + 角色 + 创建时间
- **创建用户**：用户名 + 初始密码 + 是否管理员
- **重置密码**：管理员可为任何用户重置密码
- **删除用户**：二次确认，保留至少一个管理员

#### 安全措施
- 密码使用 bcrypt 哈希
- 登录失败限制：5次/15分钟
- 至少保留一个管理员账号

---

## 错误处理

### 前端验证
- URL 格式验证
- 必填字段检查
- 重复用户名检查
- 实时反馈

### 后端验证
- 所有前端验证重复执行
- 数据库约束验证
- 权限验证

### 错误提示
- 自定义 404/500 页面
- 表单字段级错误提示
- 操作成功/失败通知

---

## 用户体验优化

### 性能优化
- Favicon 缓存到本地
- 静态资源 CDN 加速
- 数据库索引：user_id、group_id、order
- 书签超过 50 个时分页

### 交互优化
- 异步操作显示加载动画
- 删除操作模态框确认
- 拖拽半透明占位符
- 自动保存提示

---

## 部署方案

### 项目结构
```
bookmarks/
├── app.py              # Flask 应用入口
├── config.py           # 配置文件
├── requirements.txt    # 依赖列表
├── models.py           # 数据库模型
├── routes/
│   ├── auth.py        # 认证路由
│   ├── frontend.py    # 前台路由
│   ├── admin.py       # 后台路由
├── templates/          # Jinja2 模板
│   ├── base.html
│   ├── login.html
│   ├── dashboard.html
│   ├── admin/
├── static/
│   ├── css/
│   ├── js/
│   └── favicons/
├── instance/
│   └── bookmarks.db
└── logs/
```

### 服务器配置

#### Nginx
- 监听 80/443 端口
- 静态文件直接服务
- 动态请求转发到 Gunicorn (127.0.0.1:8000)
- HTTPS 支持（Let's Encrypt）
- Gzip 压缩

#### Gunicorn
- 4 个 worker 进程
- 监听 127.0.0.1:8000
- 30 秒超时
- 访问日志和错误日志

#### Systemd 服务
- 自动启动
- 进程崩溃自动重启
- 日志管理

### 初始化步骤
1. 克隆代码到服务器
2. 安装 Python 依赖
3. 初始化数据库
4. 创建第一个管理员账号
5. 配置 Nginx 和 Systemd
6. 启动服务

### 数据备份
- 每日自动备份 SQLite 文件（cron）
- 保留最近 7 天备份
- 日志轮转：每周轮转，保留 4 周

---

## 关键决策记录

1. **选择 Flask + Jinja2**：轻量级，部署简单，适合中小规模应用
2. **SQLite 数据库**：无需额外数据库服务，适合单服务器部署
3. **邀请制用户管理**：提高安全性，控制用户数量
4. **服务端渲染**：SEO 友好，降低前端复杂度
5. **SortableJS 实现拖拽**：成熟稳定，无需自己实现拖拽逻辑

---

## 未来扩展方向

- 书签导入/导出（HTML、JSON 格式）
- 书签搜索功能
- 书签标签系统
- 深色模式支持
- Docker 容器化部署
- 多语言支持
