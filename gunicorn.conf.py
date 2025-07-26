# Gunicorn configuration file for GoWith Django application
# 用于生产环境部署的Gunicorn配置

import multiprocessing
import os
from pathlib import Path

# 基础配置
bind = "0.0.0.0:8000"  # 绑定地址和端口
backlog = 2048  # 等待连接的最大数量

# Worker 配置
workers = multiprocessing.cpu_count() * 2 + 1  # Worker进程数量
worker_class = "sync"  # Worker类型
worker_connections = 1000  # 每个worker的最大并发连接数
max_requests = 1000  # 每个worker处理的最大请求数
max_requests_jitter = 50  # 最大请求数的随机抖动
preload_app = True  # 预加载应用

# 超时配置
timeout = 30  # Worker超时时间（秒）
keepalive = 2  # Keep-Alive连接的超时时间
graceful_timeout = 30  # 优雅关闭的超时时间

# 进程管理
user = None  # 运行用户（生产环境建议设置为非root用户）
group = None  # 运行用户组
tmp_upload_dir = None  # 临时上传目录

# 日志配置
loglevel = "info"  # 日志级别
accesslog = "-"  # 访问日志输出到stdout
errorlog = "-"  # 错误日志输出到stderr
access_log_format = '%(h)s %(l)s %(u)s %(t)s "%(r)s" %(s)s %(b)s "%(f)s" "%(a)s" %(D)s'

# SSL配置（如果需要HTTPS）
# keyfile = "/path/to/keyfile"
# certfile = "/path/to/certfile"

# 进程名称
proc_name = "gowith_django"

# PID文件
pidfile = "/tmp/gowith.pid"

# 环境变量
raw_env = [
    "DJANGO_SETTINGS_MODULE=gowith.settings",
]

# 钩子函数
def when_ready(server):
    """服务器启动完成时的回调"""
    server.log.info("GoWith Django application is ready to serve requests")

def worker_int(worker):
    """Worker进程接收到SIGINT信号时的回调"""
    worker.log.info("Worker received INT or QUIT signal")

def pre_fork(server, worker):
    """Worker进程fork之前的回调"""
    server.log.info("Worker spawned (pid: %s)", worker.pid)

def post_fork(server, worker):
    """Worker进程fork之后的回调"""
    server.log.info("Worker spawned (pid: %s)", worker.pid)

def post_worker_init(worker):
    """Worker进程初始化完成后的回调"""
    worker.log.info("Worker initialized (pid: %s)", worker.pid)

def worker_abort(worker):
    """Worker进程异常退出时的回调"""
    worker.log.info("Worker aborted (pid: %s)", worker.pid)

# 开发环境配置（可选）
if os.getenv('DJANGO_DEBUG', 'False').lower() == 'true':
    # 开发环境使用较少的worker和更详细的日志
    workers = 2
    loglevel = "debug"
    reload = True  # 代码变更时自动重载
    reload_extra_files = [
        "gowith/settings.py",
        ".env",
    ]

# 生产环境优化
else:
    # 生产环境禁用调试和重载
    reload = False
    # 可以根据需要调整worker数量
    # workers = 4  # 固定worker数量