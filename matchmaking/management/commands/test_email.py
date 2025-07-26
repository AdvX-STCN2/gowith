from django.core.management.base import BaseCommand
from utils.email_utils import test_email_configuration, send_simple_email
from django.conf import settings


class Command(BaseCommand):
    help = '测试邮件配置是否正确'

    def add_arguments(self, parser):
        parser.add_argument(
            '--to',
            type=str,
            help='指定收件人邮箱地址，如果不指定则使用配置中的发件人邮箱'
        )
        parser.add_argument(
            '--subject',
            type=str,
            default='GoWith邮件配置测试',
            help='邮件主题'
        )
        parser.add_argument(
            '--message',
            type=str,
            default='这是一封测试邮件，用于验证SMTP配置是否正确。如果您收到这封邮件，说明邮件功能已正常工作。',
            help='邮件内容'
        )

    def handle(self, *args, **options):
        self.stdout.write('开始测试邮件配置...')
        
        # 显示当前邮件配置
        self.stdout.write('\n当前邮件配置:')
        self.stdout.write(f'EMAIL_BACKEND: {settings.EMAIL_BACKEND}')
        self.stdout.write(f'EMAIL_HOST: {settings.EMAIL_HOST}')
        self.stdout.write(f'EMAIL_PORT: {settings.EMAIL_PORT}')
        self.stdout.write(f'EMAIL_USE_TLS: {settings.EMAIL_USE_TLS}')
        self.stdout.write(f'EMAIL_USE_SSL: {settings.EMAIL_USE_SSL}')
        self.stdout.write(f'EMAIL_HOST_USER: {settings.EMAIL_HOST_USER}')
        self.stdout.write(f'DEFAULT_FROM_EMAIL: {settings.DEFAULT_FROM_EMAIL}')
        
        # 确定收件人
        recipient = options['to']
        if not recipient:
            recipient = settings.EMAIL_HOST_USER
            if not recipient:
                self.stdout.write(
                    self.style.ERROR('错误: 未指定收件人邮箱，且EMAIL_HOST_USER未配置')
                )
                return
        
        self.stdout.write(f'\n收件人: {recipient}')
        
        try:
            # 发送测试邮件
            result = send_simple_email(
                subject=options['subject'],
                message=options['message'],
                recipient_list=[recipient],
                fail_silently=False
            )
            
            if result > 0:
                self.stdout.write(
                    self.style.SUCCESS(f'✅ 测试邮件发送成功！已发送到 {recipient}')
                )
            else:
                self.stdout.write(
                    self.style.WARNING('⚠️ 邮件发送返回0，可能发送失败')
                )
                
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'❌ 邮件发送失败: {str(e)}')
            )
            
            # 提供一些常见问题的解决建议
            self.stdout.write('\n常见问题解决建议:')
            self.stdout.write('1. 检查.env文件中的邮件配置是否正确')
            self.stdout.write('2. 确认EMAIL_HOST_USER和EMAIL_HOST_PASSWORD是否正确')
            self.stdout.write('3. 如果使用QQ邮箱，确保使用的是授权码而不是登录密码')
            self.stdout.write('4. 检查防火墙是否阻止了SMTP端口')
            self.stdout.write('5. 确认邮件服务商的SMTP设置是否正确')