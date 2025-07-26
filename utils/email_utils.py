from django.core.mail import send_mail, EmailMultiAlternatives
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from django.conf import settings
import logging

logger = logging.getLogger(__name__)


def send_simple_email(subject, message, recipient_list, from_email=None, fail_silently=False):
    """
    发送简单的文本邮件
    
    Args:
        subject (str): 邮件主题
        message (str): 邮件内容
        recipient_list (list): 收件人列表
        from_email (str, optional): 发件人邮箱，默认使用设置中的DEFAULT_FROM_EMAIL
        fail_silently (bool): 是否静默失败
    
    Returns:
        int: 成功发送的邮件数量
    """
    if from_email is None:
        from_email = settings.DEFAULT_FROM_EMAIL
    
    try:
        return send_mail(
            subject=subject,
            message=message,
            from_email=from_email,
            recipient_list=recipient_list,
            fail_silently=fail_silently
        )
    except Exception as e:
        logger.error(f"发送邮件失败: {e}")
        if not fail_silently:
            raise
        return 0


def send_html_email(subject, html_content, recipient_list, from_email=None, text_content=None, fail_silently=False):
    """
    发送HTML邮件
    
    Args:
        subject (str): 邮件主题
        html_content (str): HTML邮件内容
        recipient_list (list): 收件人列表
        from_email (str, optional): 发件人邮箱，默认使用设置中的DEFAULT_FROM_EMAIL
        text_content (str, optional): 纯文本内容，如果不提供则从HTML中提取
        fail_silently (bool): 是否静默失败
    
    Returns:
        bool: 是否发送成功
    """
    if from_email is None:
        from_email = settings.DEFAULT_FROM_EMAIL
    
    if text_content is None:
        text_content = strip_tags(html_content)
    
    try:
        email = EmailMultiAlternatives(
            subject=subject,
            body=text_content,
            from_email=from_email,
            to=recipient_list
        )
        email.attach_alternative(html_content, "text/html")
        email.send()
        return True
    except Exception as e:
        logger.error(f"发送HTML邮件失败: {e}")
        if not fail_silently:
            raise
        return False


def send_template_email(subject, template_name, context, recipient_list, from_email=None, fail_silently=False):
    """
    使用模板发送邮件
    
    Args:
        subject (str): 邮件主题
        template_name (str): 模板文件名（不包含扩展名）
        context (dict): 模板上下文
        recipient_list (list): 收件人列表
        from_email (str, optional): 发件人邮箱，默认使用设置中的DEFAULT_FROM_EMAIL
        fail_silently (bool): 是否静默失败
    
    Returns:
        bool: 是否发送成功
    """
    if from_email is None:
        from_email = settings.DEFAULT_FROM_EMAIL
    
    try:
        # 渲染HTML模板
        html_content = render_to_string(f'emails/{template_name}.html', context)
        
        # 尝试渲染文本模板，如果不存在则从HTML提取
        try:
            text_content = render_to_string(f'emails/{template_name}.txt', context)
        except:
            text_content = strip_tags(html_content)
        
        return send_html_email(
            subject=subject,
            html_content=html_content,
            recipient_list=recipient_list,
            from_email=from_email,
            text_content=text_content,
            fail_silently=fail_silently
        )
    except Exception as e:
        logger.error(f"发送模板邮件失败: {e}")
        if not fail_silently:
            raise
        return False


def send_buddy_match_notification_email(user_email, user_name, match_info):
    """
    发送搭子匹配通知邮件
    
    Args:
        user_email (str): 用户邮箱
        user_name (str): 用户姓名
        match_info (dict): 匹配信息
    
    Returns:
        bool: 是否发送成功
    """
    subject = "GoWith - 找到新的搭子匹配！"
    
    context = {
        'user_name': user_name,
        'match_info': match_info,
        'platform_name': 'GoWith平台'
    }
    
    # 如果没有模板，使用简单的HTML内容
    html_content = f"""
    <html>
    <body>
        <h2>Hi {user_name}，</h2>
        <p>恭喜！我们为您找到了新的搭子匹配。</p>
        <div style="background-color: #f5f5f5; padding: 15px; margin: 10px 0; border-radius: 5px;">
            <h3>匹配信息：</h3>
            <p><strong>活动：</strong>{match_info.get('event_title', '未知活动')}</p>
            <p><strong>匹配用户：</strong>{match_info.get('matched_user', '未知用户')}</p>
            <p><strong>匹配度：</strong>{match_info.get('compatibility_score', 0)}%</p>
        </div>
        <p>快去平台查看详细信息并联系您的新搭子吧！</p>
        <p>祝您玩得愉快！</p>
        <p>GoWith团队</p>
    </body>
    </html>
    """
    
    return send_html_email(
        subject=subject,
        html_content=html_content,
        recipient_list=[user_email],
        fail_silently=True
    )


def test_email_configuration():
    """
    测试邮件配置是否正确
    
    Returns:
        dict: 测试结果
    """
    try:
        # 发送测试邮件到管理员邮箱
        admin_email = getattr(settings, 'ADMINS', [])
        if admin_email:
            admin_email = admin_email[0][1]  # 获取第一个管理员的邮箱
        else:
            admin_email = settings.EMAIL_HOST_USER
        
        if not admin_email:
            return {
                'success': False,
                'message': '未配置管理员邮箱或发件人邮箱'
            }
        
        result = send_simple_email(
            subject='GoWith邮件配置测试',
            message='这是一封测试邮件，用于验证SMTP配置是否正确。如果您收到这封邮件，说明邮件功能已正常工作。',
            recipient_list=[admin_email],
            fail_silently=False
        )
        
        return {
            'success': True,
            'message': f'测试邮件已发送到 {admin_email}',
            'sent_count': result
        }
    except Exception as e:
        return {
            'success': False,
            'message': f'邮件配置测试失败: {str(e)}'
        }