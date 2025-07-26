from django.db import models
from django.contrib.auth import get_user_model

User = get_user_model()

class Address(models.Model):
    country = models.CharField(max_length=50, default='中国', help_text='国家')
    province = models.CharField(max_length=50, help_text='省份/直辖市')
    city = models.CharField(max_length=50, help_text='城市')
    district = models.CharField(max_length=50, blank=True, null=True, help_text='区/县')
    detailed_address = models.CharField(max_length=200, blank=True, null=True, help_text='详细地址')
    

    latitude = models.DecimalField(max_digits=10, decimal_places=7, blank=True, null=True, help_text='纬度')
    longitude = models.DecimalField(max_digits=10, decimal_places=7, blank=True, null=True, help_text='经度')
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = '地址'
        verbose_name_plural = '地址'

        indexes = [
            models.Index(fields=['city']),
            models.Index(fields=['province', 'city']),
            models.Index(fields=['city', 'district']),
        ]
    
    def __str__(self):
        return self.get_full_address()
    
    def get_full_address(self):
        parts = [self.country, self.province, self.city]
        if self.district:
            parts.append(self.district)
        if self.detailed_address:
            parts.append(self.detailed_address)
        return ' '.join(parts)
    
    def get_location_display(self):
        parts = [self.country, self.province, self.city]
        if self.district:
            parts.append(self.district)
        return ' '.join(parts)
    
    def is_same_city(self, other_address):
        return (self.province == other_address.province and 
                self.city == other_address.city)
    
    def is_same_district(self, other_address):
        return (self.is_same_city(other_address) and 
                self.district == other_address.district)
    
    def get_users_in_this_location(self):
        return self.user_profiles.all()
    
    def get_users_count(self):
        return self.user_profiles.count()
    
    @classmethod
    def get_or_create_address(cls, country='中国', province=None, city=None, district=None, detailed_address=None, latitude=None, longitude=None):
        if not province or not city:
            raise ValueError("省份和城市是必需的")
        
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
        if not created and latitude and longitude and not address.latitude:
            address.latitude = latitude
            address.longitude = longitude
            address.save()
        
        return address, created
    
    @classmethod
    def get_location_statistics(cls, country='中国', province=None, city=None):
        from django.db.models import Count
        
        filters = {'country': country}
        if province:
            filters['province'] = province
        if city:
            filters['city'] = city
        
        return cls.objects.filter(**filters).annotate(
            user_count=Count('user_profiles')
        ).order_by('-user_count')
   
