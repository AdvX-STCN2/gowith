# GoWith 邮件功能配置指南

本文档介绍如何在 GoWith 平台中配置和使用 SMTP 邮件功能。

## 配置步骤

### 1. 环境变量配置

在 `.env` 文件中添加以下邮件配置项：

```env
# SMTP邮件配置
EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
EMAIL_HOST=smtp.qq.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=your_email@qq.com
EMAIL_HOST_PASSWORD=your_app_password
DEFAULT_FROM_EMAIL=GoWith平台 <your_email@qq.com>
```

### 2. 常用邮件服务商配置

#### QQ邮箱
```env
EMAIL_HOST=smtp.qq.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=your_email@qq.com
EMAIL_HOST_PASSWORD=your_authorization_code  # 注意：这里是授权码，不是登录密码
```

#### 163邮箱
```env
EMAIL_HOST=smtp.163.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=your_email@163.com
EMAIL_HOST_PASSWORD=your_authorization_code
```

#### Gmail
```env
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=your_email@gmail.com
EMAIL_HOST_PASSWORD=your_app_password
```

#### 企业邮箱（以腾讯企业邮箱为例）
```env
EMAIL_HOST=smtp.exmail.qq.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=your_email@your_domain.com
EMAIL_HOST_PASSWORD=your_password
```

### 3. 获取邮箱授权码

#### QQ邮箱授权码获取步骤：
1. 登录QQ邮箱
2. 点击「设置」→「账户」
3. 找到「POP3/IMAP/SMTP/Exchange/CardDAV/CalDAV服务」
4. 开启「POP3/SMTP服务」或「IMAP/SMTP服务」
5. 按照提示发送短信，获取授权码
6. 将授权码填入 `EMAIL_HOST_PASSWORD`

#### 163邮箱授权码获取步骤：
1. 登录163邮箱
2. 点击「设置」→「POP3/SMTP/IMAP」
3. 开启「POP3/SMTP服务」
4. 设置客户端授权密码
5. 将授权密码填入 `EMAIL_HOST_PASSWORD`

## 测试邮件配置

### 使用管理命令测试

```bash
# 测试邮件配置（发送到配置的发件人邮箱）
python manage.py test_email

# 发送测试邮件到指定邮箱
python manage.py test_email --to recipient@example.com

# 自定义邮件主题和内容
python manage.py test_email --to recipient@example.com --subject "测试邮件" --message "这是测试内容"
```

### 使用Python代码测试

```python
from utils.email_utils import test_email_configuration, send_simple_email

# 测试邮件配置
result = test_email_configuration()
print(result)

# 发送简单邮件
send_simple_email(
    subject='测试邮件',
    message='这是一封测试邮件',
    recipient_list=['recipient@example.com']
)
```

## 邮件功能使用

### 1. 发送简单文本邮件

```python
from utils.email_utils import send_simple_email

result = send_simple_email(
    subject='邮件主题',
    message='邮件内容',
    recipient_list=['user1@example.com', 'user2@example.com']
)
```

### 2. 发送HTML邮件

```python
from utils.email_utils import send_html_email

html_content = """
<html>
<body>
    <h2>欢迎使用GoWith平台</h2>
    <p>这是一封HTML邮件</p>
</body>
</html>
"""

result = send_html_email(
    subject='HTML邮件',
    html_content=html_content,
    recipient_list=['user@example.com']
)
```

### 3. 发送搭子匹配通知

```python
from utils.email_utils import send_buddy_match_notification_email

match_info = {
    'event_title': '周末爬山',
    'matched_user': '张三',
    'compatibility_score': 85
}

result = send_buddy_match_notification_email(
    user_email='user@example.com',
    user_name='李四',
    match_info=match_info
)
```

## 当前系统集成

邮件功能已集成到以下场景：

1. **搭子匹配通知**：当系统为用户找到匹配的搭子时，会自动发送邮件通知
2. **Celery异步任务**：邮件发送通过Celery异步处理，不会阻塞主要业务流程

### 搭子匹配邮件流程

1. 用户创建搭子请求
2. 系统运行匹配算法
3. 找到匹配后创建匹配记录
4. 异步发送邮件通知给**发起请求的用户**
5. 用户收到邮件，了解匹配结果

## 故障排除

### 常见问题

1. **邮件发送失败**
   - 检查网络连接
   - 确认SMTP服务器地址和端口
   - 验证用户名和密码/授权码

2. **授权失败**
   - 确保使用授权码而不是登录密码
   - 检查邮箱是否开启了SMTP服务

3. **连接超时**
   - 检查防火墙设置
   - 尝试不同的端口（25, 465, 587）
   - 检查TLS/SSL设置

4. **邮件被拒绝**
   - 检查发件人邮箱是否被列入黑名单
   - 确认邮件内容不包含敏感词汇
   - 检查发送频率是否过高

### 调试模式

在开发环境中，可以使用控制台后端来调试邮件：

```env
# 开发环境：邮件输出到控制台
EMAIL_BACKEND=django.core.mail.backends.console.EmailBackend
```

### 日志查看

邮件发送的详细日志可以在以下位置查看：
- Django日志
- Celery worker日志

```bash
# 查看Celery日志
celery -A gowith worker --loglevel=info
```

## 安全建议

1. **保护邮箱密码**：使用授权码而不是真实密码
2. **限制发送频率**：避免被邮件服务商标记为垃圾邮件
3. **使用TLS加密**：确保邮件传输安全
4. **定期更新授权码**：定期更换邮箱授权码
5. **监控发送状态**：及时发现和处理发送失败的邮件

## 扩展功能

未来可以考虑添加的功能：

1. **邮件模板系统**：支持HTML模板和样式
2. **邮件队列管理**：更精细的邮件发送控制
3. **邮件统计**：发送成功率、打开率等统计
4. **多邮件服务商支持**：自动切换邮件服务商
5. **邮件内容个性化**：根据用户偏好定制邮件内容