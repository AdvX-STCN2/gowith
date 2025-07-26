# GoWith Backend

> **GoWith: Your City, Your Activities, Your Companions.**

GoWith是一个搭子匹配平台，旨在为用户寻找共同活动伙伴提供无缝连接体验。本仓库是后端仓库。

## 🌟 产品特色

### 核心理念
GoWith专注于真实连接和安全互动，而非基于聊天的沟通方式，帮助用户轻松找到志同道合的活动伙伴。

### 品牌关键词
- **Connect** - 连接志趣相投的人
- **Local** - 专注本地化体验
- **Activity-focused** - 以活动为中心
- **Effortless** - 无摩擦的使用体验

## 🎯 解决的核心问题

1. **寻找特定活动的志同道合伙伴困难**
   - 个人往往难以找到有相似兴趣或时间安排的人参与特定本地活动

2. **本地活动和伙伴发现效率低下**
   - 用户难以同时发现相关的本地活动并找到合适的参与伙伴

## 👥 目标用户

### 活动爱好者 (15-35岁)
- 对特定爱好充满热情（如徒步、桌游、音乐会、黑客松）
- 缺乏稳定的活动伙伴或希望扩展活动圈子

### 新居民/探索者 (20-30岁)
- 新迁入城市或希望深入了解当地文化
- 渴望探索本地景点并结识新朋友

### 社区建设者/组织者 (30-50岁)
- 定期参与或组织小众活动
- 希望找到可靠的新成员加入既定或临时活动

## 🏗️ 技术架构

### 后端技术栈
- **框架**: Django 5.2 + Django REST Framework
- **数据库**: PostgreSQL
- **认证**: Casdoor SSO集成
- **异步任务**: Celery + Redis
- **API文档**: drf-spectacular (OpenAPI 3.0)
- **邮件服务**: SMTP集成
- **AI集成**: 智能匹配算法

## 🚀 快速开始

### 环境要求
- Python 3.11+
- PostgreSQL 13+
- Redis 6+
- Node.js 22+ (用于前端，如需要)

### 安装步骤

1. **克隆仓库**
   ```bash
   git clone <repository-url>
   cd <folder>
   ```

2. **安装依赖**
   ```bash
   pdm install
   ```

3. **环境配置**
   ```bash
   cp .env.example .env
   # 编辑.env文件，配置数据库、Redis、Casdoor等
   ```

4. **数据库设置**
   ```bash
   pdm run python manage.py migrate
   # pdm run python manage.py createsuperuser # 如果你需要创建 Django Admin 管理员账号
   ```

5. **启动服务**
   ```bash
   # 启动Django开发服务器
   pdm run python manage.py runserver
   
   # 启动Celery Worker (新终端)
   pdm run celery -A gowith worker --loglevel=info
   
   # 启动Celery Beat (新终端，如需定时任务)
   pdm run celery -A gowith beat --loglevel=info
   ```

## ⚙️ 配置说明

### 环境变量配置

创建`.env`文件并配置以下变量：

```env
# Django配置
SECRET_KEY=your-secret-key
DEBUG=True

# 数据库配置
DB_NAME=gowith_db
DB_USER=postgres
DB_PASSWORD=your-password
DB_HOST=localhost
DB_PORT=5432

# Casdoor SSO配置
CASDOOR_ENDPOINT=https://your-casdoor-instance
CASDOOR_CLIENT_ID=your-client-id
CASDOOR_CLIENT_SECRET=your-client-secret
CASDOOR_ORGANIZATION_NAME=your-org
CASDOOR_APPLICATION_NAME=your-app

# Celery配置
CELERY_BROKER_URL=redis://localhost:6379/0
CELERY_RESULT_BACKEND=redis://localhost:6379/0

# SMTP邮件配置
EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
EMAIL_HOST=smtp.qq.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=your_email@qq.com
EMAIL_HOST_PASSWORD=your_app_password
DEFAULT_FROM_EMAIL=GoWith平台 <your_email@qq.com>

# AI服务配置
AI_TOKEN=your-ai-service-token
```

### Casdoor集成

GoWith使用Casdoor作为统一身份认证服务：

1. 部署Casdoor实例
2. 创建应用程序配置
3. 配置回调URL和权限
4. 更新`.env`文件中的Casdoor配置

详细配置请参考：[Casdoor官方文档](https://casdoor.org/docs/)

## 📊 API文档

启动服务后，可通过以下地址访问API文档：

- **Swagger UI**: `http://localhost:8000/api/schema/swagger-ui/`
- **ReDoc**: `http://localhost:8000/api/schema/redoc/`
- **OpenAPI Schema**: `http://localhost:8000/api/schema/`

### 主要API端点

- `/api/auth/` - 认证相关
- `/api/profiles/` - 用户档案管理
- `/api/events/` - 活动管理
- `/api/matchmaking/` - 搭子匹配
- `/admin/` - Django管理后台

## 🔧 开发工具

### 管理命令

```bash
# 测试邮件配置
python manage.py test_email

# 数据库迁移
python manage.py makemigrations
python manage.py migrate

# 创建超级用户
python manage.py createsuperuser

# 收集静态文件
python manage.py collectstatic
```

### 代码质量

```bash
# 代码格式化
black .

# 代码检查
flake8 .

# 类型检查
mypy .

# 运行测试
python manage.py test
```

## 🚀 部署指南

### 生产环境部署

1. **服务器准备**
   - Ubuntu 22.04+
   - Python 3.12+
   - PostgreSQL 13+
   - Redis 6+
   - Nginx/Caddy

2. **应用部署**

请参照其他 Django 项目部署流程，使用任意方式部署即可。此处不再提供具体教程。


## 🤝 贡献指南

1. Fork本仓库
2. 创建特性分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 创建Pull Request

## 📄 许可证

本项目采用GPL 3.0许可证 - 查看 [LICENCE](LICENCE) 文件了解详情。

## 📞 支持

如有问题或建议，请通过以下方式联系：

- 创建Issue
- 发送邮件至项目维护者
- 查看文档和FAQ

---

**GoWith** - 让每一次活动都有最佳的伙伴相伴！ 🎉