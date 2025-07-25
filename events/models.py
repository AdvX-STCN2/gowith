from django.db import models
from django.contrib.auth import get_user_model
from authentication.models import Address

User = get_user_model()

class Event(models.Model):
    name = models.CharField(max_length=200, help_text='活动名称')
    start_time = models.DateTimeField(help_text='开始时间')
    end_time = models.DateTimeField(help_text='结束时间')
    location = models.ForeignKey(Address, on_delete=models.SET_NULL, null=True, blank=True, 
                                related_name='events', help_text='活动地点')
    is_online = models.BooleanField(default=False, help_text='是否为线上活动')
    logo_url = models.URLField(blank=True, null=True, help_text='活动Logo URL')
    banner_url = models.URLField(blank=True, null=True, help_text='活动横幅URL')
    introduction = models.TextField(blank=True, null=True, help_text='活动描述')
    creator = models.ForeignKey(User, on_delete=models.CASCADE, related_name='created_events',
                               help_text='活动创建者')
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = '活动'
        verbose_name_plural = '活动'
        indexes = [
            models.Index(fields=['start_time']),
            models.Index(fields=['location']),
            models.Index(fields=['creator']),
        ]
    
    def __str__(self):
        return self.name
    
    def get_participant_count(self):
        return self.buddy_requests.count()
    
    def get_buddy_requests(self):
        return self.buddy_requests.all()
    
    def get_open_buddy_requests(self):
        return self.buddy_requests.filter(status='open')
    
    def get_buddy_requests_by_activity_type(self, activity_type):
        return self.buddy_requests.filter(activity_type=activity_type)
    
    def has_buddy_request_from_user(self, user):
        return self.buddy_requests.filter(user=user).exists()
