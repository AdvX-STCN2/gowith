import os
from celery import Celery
from django.conf import settings

# 设置Django设置模块
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'gowith.settings')

# 创建Celery应用实例
app = Celery('gowith')

# 使用Django设置配置Celery
app.config_from_object('django.conf:settings', namespace='CELERY')

# 自动发现任务
app.autodiscover_tasks()

# 可选：添加调试任务
@app.task(bind=True)
def debug_task(self):
    print(f'Request: {self.request!r}')