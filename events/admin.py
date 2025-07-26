from django.contrib import admin
from .models import Event

@admin.register(Event)
class EventAdmin(admin.ModelAdmin):
    list_display = ('name', 'start_time', 'end_time', 'location', 'is_online', 'creator', 'created_at')
    list_filter = ('is_online', 'start_time', 'end_time', 'creator', 'location__city')
    search_fields = ('name', 'introduction', 'description', 'creator__username')
    readonly_fields = ('created_at',)
    ordering = ('-start_time',)
    date_hierarchy = 'start_time'
    
    fieldsets = (
        ('基本信息', {
            'fields': ('name', 'creator', 'introduction', 'description')
        }),
        ('时间安排', {
            'fields': ('start_time', 'end_time')
        }),
        ('地点信息', {
            'fields': ('location', 'is_online')
        }),
        ('媒体资源', {
            'fields': ('logo_url', 'banner_url'),
            'classes': ('collapse',)
        }),
        ('时间信息', {
            'fields': ('created_at',),
            'classes': ('collapse',)
        })
    )
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('creator', 'location')
