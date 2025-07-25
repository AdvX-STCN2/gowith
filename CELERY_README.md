# Celery 配置和使用指南

## 概述

本项目已集成 Celery 分布式任务队列，用于处理异步任务，如：
- 搭子匹配通知
- 复杂的匹配算法处理
- 定期清理过期数据
- 生成个性化推荐

## 安装和配置

### 1. 依赖已安装
- `celery>=5.3.0`
- `redis>=5.0.0`

### 2. Redis 服务器

确保 Redis 服务器正在运行：
```bash
# macOS (使用 Homebrew)
brew install redis
brew services start redis

# 或者直接启动
redis-server
```

### 3. 环境变量配置

在 `.env` 文件中已配置：
```
CELERY_BROKER_URL=redis://localhost:6379/0
CELERY_RESULT_BACKEND=redis://localhost:6379/0
```

## 启动 Celery

### 启动 Celery Worker

在项目根目录下运行：
```bash
# 启动 worker
pdm run celery -A gowith worker --loglevel=info

# 在 macOS 上可能需要添加 --pool=solo 参数
pdm run celery -A gowith worker --loglevel=info --pool=solo
```

### 启动 Celery Beat (定时任务调度器)

```bash
# 启动 beat 调度器
pdm run celery -A gowith beat --loglevel=info
```

### 启动 Flower (监控界面)

```bash
# 安装 flower
pdm add flower

# 启动监控界面
pdm run celery -A gowith flower
```

访问 http://localhost:5555 查看任务监控界面。

## 任务示例

### 1. 搭子匹配通知

```python
from matchmaking.tasks import send_buddy_match_notification

# 异步执行
result = send_buddy_match_notification.delay(
    'user@example.com',
    '张三 - 喜欢爬山和摄影'
)

# 获取任务结果
print(result.get())
```

### 2. 处理搭子匹配

```python
from matchmaking.tasks import process_buddy_matching

# 为特定活动处理匹配
result = process_buddy_matching.delay(event_id=1)
```

### 3. 清理过期请求

```python
from matchmaking.tasks import cleanup_expired_requests

# 清理过期的搭子请求
result = cleanup_expired_requests.delay()
```

## 测试任务

使用管理命令测试任务：

```bash
# 测试所有任务（同步执行）
pdm run python3 ./manage.py test_celery

# 测试特定任务
pdm run python3 ./manage.py test_celery --task=notification

# 异步执行测试（需要 worker 运行）
pdm run python3 ./manage.py test_celery --async
```

## 生产环境部署

### 1. 使用 Supervisor 管理进程

创建 `/etc/supervisor/conf.d/celery.conf`：

```ini
[program:celery]
command=/path/to/venv/bin/celery -A gowith worker --loglevel=info
directory=/path/to/project
user=www-data
numprocs=1
stdout_logfile=/var/log/celery/worker.log
stderr_logfile=/var/log/celery/worker.log
autostart=true
autorestart=true
startsecs=10
stopwaitsecs=600
killasgroup=true
priority=998

[program:celerybeat]
command=/path/to/venv/bin/celery -A gowith beat --loglevel=info
directory=/path/to/project
user=www-data
numprocs=1
stdout_logfile=/var/log/celery/beat.log
stderr_logfile=/var/log/celery/beat.log
autostart=true
autorestart=true
startsecs=10
stopwaitsecs=600
killasgroup=true
priority=999
```

### 2. 使用 systemd 管理服务

创建 `/etc/systemd/system/celery.service`：

```ini
[Unit]
Description=Celery Service
After=network.target

[Service]
Type=forking
User=www-data
Group=www-data
EnvironmentFile=/path/to/project/.env
WorkingDirectory=/path/to/project
ExecStart=/path/to/venv/bin/celery -A gowith worker --detach
ExecStop=/path/to/venv/bin/celery -A gowith control shutdown
ExecReload=/bin/kill -s HUP $MAINPID
KillMode=mixed
TimeoutStopSec=300

[Install]
WantedBy=multi-user.target
```

## 监控和日志

### 1. 查看任务状态

```python
from celery.result import AsyncResult

result = AsyncResult('task-id')
print(result.status)  # PENDING, SUCCESS, FAILURE, etc.
print(result.result)  # 任务结果
```

### 2. 日志配置

在 Django settings 中配置日志：

```python
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'celery': {
            'level': 'INFO',
            'class': 'logging.FileHandler',
            'filename': 'celery.log',
        },
    },
    'loggers': {
        'celery': {
            'handlers': ['celery'],
            'level': 'INFO',
        },
    },
}
```

## 常见问题

### 1. macOS 上的兼容性问题

如果遇到 fork 相关错误，使用 `--pool=solo` 参数：
```bash
pdm run celery -A gowith worker --loglevel=info --pool=solo
```

### 2. Redis 连接问题

检查 Redis 是否运行：
```bash
redis-cli ping
```

### 3. 任务不执行

确保：
- Redis 服务正在运行
- Celery worker 已启动
- 任务模块已正确导入

## 扩展功能

### 1. 任务重试

```python
@shared_task(bind=True, autoretry_for=(Exception,), retry_kwargs={'max_retries': 3})
def my_task(self):
    # 任务逻辑
    pass
```

### 2. 任务优先级

```python
@shared_task
def high_priority_task():
    pass

# 高优先级执行
high_priority_task.apply_async(priority=9)
```

### 3. 定时任务

在 settings.py 中配置：

```python
CELERY_BEAT_SCHEDULE = {
    'cleanup-expired-requests': {
        'task': 'matchmaking.tasks.cleanup_expired_requests',
        'schedule': crontab(hour=2, minute=0),  # 每天凌晨2点执行
    },
}
```