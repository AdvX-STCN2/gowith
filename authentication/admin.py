from django.contrib import admin
from .models import Address

@admin.register(Address)
class AddressAdmin(admin.ModelAdmin):
    list_display = ('get_full_address', 'province', 'city', 'district', 'created_at')
    list_filter = ('country', 'province', 'city', 'district')
    search_fields = ('province', 'city', 'district', 'detailed_address')
    readonly_fields = ('created_at', 'updated_at')
    ordering = ('-created_at',)
    
    fieldsets = (
        ('基本信息', {
            'fields': ('country', 'province', 'city', 'district', 'detailed_address')
        }),
        ('地理坐标', {
            'fields': ('latitude', 'longitude'),
            'classes': ('collapse',)
        }),
        ('时间信息', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )
