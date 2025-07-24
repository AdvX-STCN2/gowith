from django.db import models
from django.contrib.auth import get_user_model

User = get_user_model()

class Address(models.Model):
    """地址信息模型 - 封装地址相关字段"""
    country = models.CharField(max_length=50, default='中国', help_text='国家')
    province = models.CharField(max_length=50, help_text='省份/直辖市')
    city = models.CharField(max_length=50, help_text='城市')
    district = models.CharField(max_length=50, blank=True, null=True, help_text='区/县')
    detailed_address = models.CharField(max_length=200, blank=True, null=True, help_text='详细地址')
    
    # 地理坐标 - 用于精确距离计算
    latitude = models.DecimalField(max_digits=10, decimal_places=7, blank=True, null=True, help_text='纬度')
    longitude = models.DecimalField(max_digits=10, decimal_places=7, blank=True, null=True, help_text='经度')
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = '地址'
        verbose_name_plural = '地址'
        # 为同城查找添加数据库索引
        indexes = [
            models.Index(fields=['city']),
            models.Index(fields=['province', 'city']),
            models.Index(fields=['city', 'district']),
        ]
        # 添加唯一约束，防止相同地址重复存储
        # 注意：detailed_address不包含在约束中，因为详细地址可能不同
        unique_together = [
            ('country', 'province', 'city', 'district')
        ]
    
    def __str__(self):
        return self.get_full_address()
    
    def get_full_address(self):
        """获取完整地址显示"""
        parts = [self.country, self.province, self.city]
        if self.district:
            parts.append(self.district)
        if self.detailed_address:
            parts.append(self.detailed_address)
        return ' '.join(parts)
    
    def get_location_display(self):
        """获取位置显示（不包含详细地址）"""
        parts = [self.country, self.province, self.city]
        if self.district:
            parts.append(self.district)
        return ' '.join(parts)
    
    def is_same_city(self, other_address):
        """判断是否同城"""
        return (self.province == other_address.province and 
                self.city == other_address.city)
    
    def is_same_district(self, other_address):
        """判断是否同区"""
        return (self.is_same_city(other_address) and 
                self.district == other_address.district)
    
    def get_users_in_this_location(self):
        """反向查询：获取该地点的所有用户"""
        return self.user_profiles.all()
    
    def get_users_count(self):
        """获取该地点的用户数量"""
        return self.user_profiles.count()
    
    @classmethod
    def get_or_create_address(cls, country='中国', province=None, city=None, district=None, detailed_address=None, latitude=None, longitude=None):
        """获取或创建地址，避免重复存储相同地点"""
        if not province or not city:
            raise ValueError("省份和城市是必需的")
        
        # 先尝试获取已存在的地址（不包含详细地址）
        address, created = cls.objects.get_or_create(
            country=country,
            province=province,
            city=city,
            district=district,
            defaults={
                'detailed_address': detailed_address,
                'latitude': latitude,
                'longitude': longitude,
            }
        )
        
        # 如果地址已存在但坐标信息更完整，则更新
        if not created and latitude and longitude and not address.latitude:
            address.latitude = latitude
            address.longitude = longitude
            address.save()
        
        return address, created
    
    @classmethod
    def get_users_by_location(cls, country='中国', province=None, city=None, district=None):
        """根据地点查询所有用户"""
        from authentication.models import UserProfile  # 避免循环导入
        
        filters = {'address__country': country}
        if province:
            filters['address__province'] = province
        if city:
            filters['address__city'] = city
        if district:
            filters['address__district'] = district
        
        return UserProfile.objects.filter(**filters).exclude(address__isnull=True)
    
    @classmethod
    def get_location_statistics(cls, country='中国', province=None, city=None):
        """获取地点统计信息"""
        from django.db.models import Count
        from authentication.models import UserProfile
        
        filters = {'country': country}
        if province:
            filters['province'] = province
        if city:
            filters['city'] = city
        
        return cls.objects.filter(**filters).annotate(
            user_count=Count('user_profiles')
        ).order_by('-user_count')

class UserProfile(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='profiles')
    mbti = models.CharField(max_length=8)
    name = models.CharField(max_length=20)
    birthday = models.DateField()
    sex = models.CharField(max_length=10, choices=[
        ('男', '男'),
        ('女', '女'),
        ('其他', '其他')
    ], help_text='性别')
    phone = models.CharField(max_length=15)
    email = models.EmailField()
    
    # 地址信息 - 通过外键关联Address模型
    address = models.ForeignKey(Address, on_delete=models.SET_NULL, null=True, blank=True, 
                               related_name='user_profiles', help_text='用户地址')
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = '用户档案'
        verbose_name_plural = '用户档案'
    
    def __str__(self):
        city_name = self.address.city if self.address else '未知'
        return f"{self.name} - {city_name}"
    
    def get_location_display(self):
        """获取完整地址显示"""
        return self.address.get_location_display() if self.address else '未设置地址'
    
    def is_same_city(self, other_profile):
        """判断是否同城"""
        if not self.address or not other_profile.address:
            return False
        return self.address.is_same_city(other_profile.address)
    
    def is_same_district(self, other_profile):
        """判断是否同区"""
        if not self.address or not other_profile.address:
            return False
        return self.address.is_same_district(other_profile.address)
    
    @classmethod
    def create_with_address(cls, user, address_data, **profile_data):
        """创建用户档案并关联地址（避免重复地址）"""
        # 使用get_or_create_address避免重复存储
        address, created = Address.get_or_create_address(**address_data)
        
        # 创建用户档案
        profile = cls.objects.create(
            user=user,
            address=address,
            **profile_data
        )
        
        return profile, address, created
    
    @classmethod
    def get_same_city_users(cls, user_profile, exclude_self=True):
        """获取同城用户"""
        if not user_profile.address:
            return cls.objects.none()
        
        queryset = cls.objects.filter(
            address__province=user_profile.address.province,
            address__city=user_profile.address.city
        ).exclude(address__isnull=True)
        
        if exclude_self:
            queryset = queryset.exclude(id=user_profile.id)
        return queryset
    
    @classmethod
    def get_same_district_users(cls, user_profile, exclude_self=True):
        """获取同区用户"""
        if not user_profile.address or not user_profile.address.district:
            return cls.objects.none()
        
        queryset = cls.objects.filter(
            address__province=user_profile.address.province,
            address__city=user_profile.address.city,
            address__district=user_profile.address.district
        ).exclude(address__isnull=True)
        
        if exclude_self:
            queryset = queryset.exclude(id=user_profile.id)
        return queryset
    
    @classmethod
    def get_users_by_location(cls, country='中国', province=None, city=None, district=None):
        """根据地点查询所有用户（便捷方法）"""
        return Address.get_users_by_location(country, province, city, district)
   
