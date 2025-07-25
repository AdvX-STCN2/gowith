from django.db import models
from django.contrib.auth import get_user_model
from authentication.models import Address

User = get_user_model()

class UserProfile(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='profiles')
    name = models.CharField(max_length=20, help_text='档案名称')
    phone = models.CharField(max_length=15, blank=True, null=True, help_text='联系电话')
    contact_info = models.TextField(blank=True, null=True, help_text='联系方式（微信、QQ、邮箱等）')
    mbti = models.CharField(max_length=8, blank=True, null=True, help_text='MBTI性格类型')
    bio = models.TextField(blank=True, null=True, help_text='个人简介')
    avatar_url = models.URLField(blank=True, null=True, help_text='头像URL')
    

    address = models.ForeignKey(Address, on_delete=models.SET_NULL, null=True, blank=True, 
                               related_name='user_profiles', help_text='用户地址')
    

    is_active = models.BooleanField(default=True, help_text='是否激活')
    is_primary = models.BooleanField(default=False, help_text='是否为主档案')
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = '用户档案'
        verbose_name_plural = '用户档案'
        indexes = [
            models.Index(fields=['user']),
            models.Index(fields=['is_active']),
            models.Index(fields=['is_primary']),
        ]
        constraints = [
            models.UniqueConstraint(
                fields=['user'],
                condition=models.Q(is_primary=True),
                name='unique_primary_profile_per_user'
            )
        ]
    
    def __str__(self):
        city_name = self.address.city if self.address else '未知'
        return f"{self.name} - {city_name}"
    
    def get_location_display(self):
        return self.address.get_location_display() if self.address else '未设置地址'
    
    def is_same_city(self, other_profile):
        if not self.address or not other_profile.address:
            return False
        return self.address.is_same_city(other_profile.address)
    
    def is_same_district(self, other_profile):
        if not self.address or not other_profile.address:
            return False
        return self.address.is_same_district(other_profile.address)
    
    def save(self, *args, **kwargs):
        if not self.pk and not self.user.profiles.exists():
            self.is_primary = True
        if self.is_primary:
            self.user.profiles.filter(is_primary=True).exclude(pk=self.pk).update(is_primary=False)
        
        super().save(*args, **kwargs)
    
    @classmethod
    def create_with_address(cls, user, address_data, **profile_data):
        address, created = Address.get_or_create_address(**address_data)
        profile = cls.objects.create(
            user=user,
            address=address,
            **profile_data
        )
        
        return profile, address, created
    
    @classmethod
    def get_same_city_users(cls, user_profile, exclude_self=True):
        if not user_profile.address:
            return cls.objects.none()
        
        queryset = cls.objects.filter(
            address__province=user_profile.address.province,
            address__city=user_profile.address.city,
            is_active=True
        ).exclude(address__isnull=True)
        
        if exclude_self:
            queryset = queryset.exclude(id=user_profile.id)
        return queryset
