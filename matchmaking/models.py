from django.db import models
from django.contrib.auth import get_user_model
from events.models import Event
from profiles.models import UserProfile

User = get_user_model()

class BuddyRequest(models.Model):
    STATUS_CHOICES = [
        ('open', '开放'),
        ('closed', '关闭'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='buddy_requests')
    profile = models.ForeignKey(UserProfile, on_delete=models.CASCADE, related_name='buddy_requests', help_text='使用的用户档案', null=True, blank=True)
    event = models.ForeignKey(Event, on_delete=models.CASCADE, related_name='buddy_requests')
    description = models.TextField(help_text='描述')

    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='open', help_text='状态')
    celery_task_id = models.CharField(max_length=255, blank=True, null=True, help_text='Celery任务ID')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = '搭子请求'
        verbose_name_plural = '搭子请求'
        indexes = [
            models.Index(fields=['user']),
            models.Index(fields=['profile']),
            models.Index(fields=['event']),
            models.Index(fields=['status']),
        ]
    
    def __str__(self):
        return f"{self.profile.name} - {self.event.name}"
    
    def get_current_participants_count(self):
        return self.matches.filter(status='accepted').count() + 1
    

    
    def can_join(self, user):
        if self.user == user:
            return False
        if self.status != 'open':
            return False

        if self.matches.filter(matched_user=user).exists():
            return False
        return True
    
    def save(self, *args, **kwargs):
        if self.profile and self.profile.user != self.user:
            raise ValueError("档案必须属于当前用户")
        super().save(*args, **kwargs)

class BuddyRequestTag(models.Model):
    request = models.ForeignKey(BuddyRequest, on_delete=models.CASCADE, related_name='tags')
    tag_name = models.CharField(max_length=50, help_text='标签名称（如：编程、组队）')
    
    class Meta:
        verbose_name = '搭子请求标签'
        verbose_name_plural = '搭子请求标签'
        unique_together = [('request', 'tag_name')]
        indexes = [
            models.Index(fields=['tag_name']),
            models.Index(fields=['request']),
        ]
    
    def __str__(self):
        return f"{self.request.event.name} - {self.tag_name}"

class BuddyMatch(models.Model):
    STATUS_CHOICES = [
        ('pending', '待确认'),
        ('accepted', '已接受'),
        ('rejected', '已拒绝'),
    ]
    
    request = models.ForeignKey(BuddyRequest, on_delete=models.CASCADE, related_name='matches')
    matched_user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='buddy_matches')
    matched_at = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='pending', help_text='匹配状态')
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = '搭子匹配'
        verbose_name_plural = '搭子匹配'
        unique_together = [('request', 'matched_user')]
        indexes = [
            models.Index(fields=['request']),
            models.Index(fields=['matched_user']),
            models.Index(fields=['status']),
            models.Index(fields=['matched_at']),
        ]
    
    def __str__(self):
        return f"{self.matched_user.username} -> {self.request.event.name} ({self.status})"

class UserFeedback(models.Model):
    from_user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='given_feedbacks')
    to_user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='received_feedbacks')
    rating = models.PositiveSmallIntegerField(choices=[
        (1, '1星'),
        (2, '2星'),
        (3, '3星'),
        (4, '4星'),
        (5, '5星'),
    ], help_text='评分（1-5星）')
    comment = models.TextField(blank=True, null=True, help_text='评价内容')
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = '用户反馈'
        verbose_name_plural = '用户反馈'
        unique_together = [('from_user', 'to_user')]
        indexes = [
            models.Index(fields=['from_user']),
            models.Index(fields=['to_user']),
            models.Index(fields=['rating']),
            models.Index(fields=['created_at']),
        ]
    
    def __str__(self):
        return f"{self.from_user.username} -> {self.to_user.username} ({self.rating}星)"
    
    @classmethod
    def get_user_average_rating(cls, user):
        from django.db.models import Avg
        result = cls.objects.filter(to_user=user).aggregate(avg_rating=Avg('rating'))
        return result['avg_rating'] or 0
    
    @classmethod
    def get_user_feedback_count(cls, user):
        return cls.objects.filter(to_user=user).count()
