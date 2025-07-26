备忘 如何跑celery


## Celery 启动指南
根据项目配置，以下是启动 Celery 的完整步骤：

### 前置条件
1. 1.
   确保 Redis 服务运行 ：
### 启动 Celery 服务
1. 启动 Celery Worker（处理异步任务） ：

```
# 基本启动命令
pdm run celery -A gowith worker --loglevel=info

# macOS 系统推荐使用（避免 fork 问题）
pdm run celery -A gowith worker --loglevel=info --pool=solo
```

2. 启动 Celery Beat（定时任务调度器） ：

```
pdm run celery -A gowith beat --loglevel=info
```

3. 启动 Flower（可选，监控界面） ：

```
# 先安装 flower
pdm add flower

# 启动监控界面
pdm run celery -A gowith flower
```