from django.contrib import admin
from .models import UserProfile

@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ('name', 'user', 'mbti', 'phone', 'is_active', 'is_primary', 'created_at')
    list_filter = ('mbti', 'is_active', 'is_primary', 'address__city', 'created_at')
    search_fields = ('name', 'user__username', 'bio', 'phone')
    readonly_fields = ('created_at', 'updated_at')
    ordering = ('-created_at',)
    
    fieldsets = (
        ('基本信息', {
            'fields': ('user', 'name', 'phone', 'contact_info')
        }),
        ('个人资料', {
            'fields': ('mbti', 'bio', 'avatar_url')
        }),
        ('地址信息', {
            'fields': ('address',)
        }),
        ('状态设置', {
            'fields': ('is_active', 'is_primary')
        }),
        ('时间信息', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('user', 'address')
