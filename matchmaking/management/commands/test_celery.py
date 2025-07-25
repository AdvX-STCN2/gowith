from django.core.management.base import BaseCommand
from matchmaking.tasks import (
    send_buddy_match_notification,
    process_buddy_matching,
    cleanup_expired_requests,
    generate_activity_recommendations
)

class Command(BaseCommand):
    help = '测试Celery任务'

    def add_arguments(self, parser):
        parser.add_argument(
            '--task',
            type=str,
            choices=['notification', 'matching', 'cleanup', 'recommendations', 'all'],
            default='all',
            help='要测试的任务类型'
        )
        parser.add_argument(
            '--async',
            action='store_true',
            help='异步执行任务（需要Celery worker运行）'
        )

    def handle(self, *args, **options):
        task_type = options['task']
        is_async = options['async']
        
        self.stdout.write(self.style.SUCCESS('开始测试Celery任务...'))
        
        if task_type in ['notification', 'all']:
            self.test_notification_task(is_async)
            
        if task_type in ['matching', 'all']:
            self.test_matching_task(is_async)
            
        if task_type in ['cleanup', 'all']:
            self.test_cleanup_task(is_async)
            
        if task_type in ['recommendations', 'all']:
            self.test_recommendations_task(is_async)
            
        self.stdout.write(self.style.SUCCESS('Celery任务测试完成！'))

    def test_notification_task(self, is_async):
        self.stdout.write('测试搭子匹配通知任务...')
        
        if is_async:
            result = send_buddy_match_notification.delay(
                'test@example.com',
                '张三 - 喜欢爬山和摄影'
            )
            self.stdout.write(f'异步任务已提交，任务ID: {result.id}')
        else:
            result = send_buddy_match_notification(
                'test@example.com',
                '张三 - 喜欢爬山和摄影'
            )
            self.stdout.write(f'同步执行结果: {result}')

    def test_matching_task(self, is_async):
        self.stdout.write('测试搭子匹配算法任务...')
        
        # 这里需要一个真实的活动ID，或者创建一个测试活动
        from events.models import Event
        
        try:
            event = Event.objects.first()
            if event:
                if is_async:
                    result = process_buddy_matching.delay(event.id)
                    self.stdout.write(f'异步任务已提交，任务ID: {result.id}')
                else:
                    result = process_buddy_matching(event.id)
                    self.stdout.write(f'同步执行结果: {result}')
            else:
                self.stdout.write(self.style.WARNING('没有找到活动，跳过匹配任务测试'))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'匹配任务测试失败: {e}'))

    def test_cleanup_task(self, is_async):
        self.stdout.write('测试清理过期请求任务...')
        
        if is_async:
            result = cleanup_expired_requests.delay()
            self.stdout.write(f'异步任务已提交，任务ID: {result.id}')
        else:
            result = cleanup_expired_requests()
            self.stdout.write(f'同步执行结果: {result}')

    def test_recommendations_task(self, is_async):
        self.stdout.write('测试活动推荐任务...')
        
        from django.contrib.auth.models import User
        
        try:
            user = User.objects.first()
            if user:
                if is_async:
                    result = generate_activity_recommendations.delay(user.id)
                    self.stdout.write(f'异步任务已提交，任务ID: {result.id}')
                else:
                    result = generate_activity_recommendations(user.id)
                    self.stdout.write(f'同步执行结果: {result}')
            else:
                self.stdout.write(self.style.WARNING('没有找到用户，跳过推荐任务测试'))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'推荐任务测试失败: {e}'))