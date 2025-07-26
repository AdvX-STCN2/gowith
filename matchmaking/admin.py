from django.contrib import admin
from .models import BuddyRequest, BuddyRequestTag, BuddyMatch, UserFeedback

@admin.register(BuddyRequest)
class BuddyRequestAdmin(admin.ModelAdmin):
    list_display = ('__str__', 'user', 'event', 'is_public', 'created_at')
    list_filter = ('is_public', 'event__name', 'created_at', 'event__start_time')
    search_fields = ('description', 'user__username', 'event__name', 'profile__name')
    readonly_fields = ('created_at', 'updated_at', 'celery_task_id')
    ordering = ('-created_at',)
    date_hierarchy = 'created_at'
    
    fieldsets = (
        ('基本信息', {
            'fields': ('user', 'profile', 'event')
        }),
        ('请求详情', {
            'fields': ('description', 'is_public')
        }),
        ('系统信息', {
            'fields': ('celery_task_id', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('user', 'profile', 'event')

@admin.register(BuddyRequestTag)
class BuddyRequestTagAdmin(admin.ModelAdmin):
    list_display = ('tag_name', 'request', 'request_user', 'request_event')
    list_filter = ('tag_name', 'request__event__name')
    search_fields = ('tag_name', 'request__description', 'request__user__username')
    ordering = ('tag_name',)
    
    def request_user(self, obj):
        return obj.request.user.username
    request_user.short_description = '请求用户'
    
    def request_event(self, obj):
        return obj.request.event.name
    request_event.short_description = '活动名称'
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('request__user', 'request__event')

@admin.register(BuddyMatch)
class BuddyMatchAdmin(admin.ModelAdmin):
    list_display = ('__str__', 'request', 'matched_user', 'status', 'matched_at')
    list_filter = ('status', 'matched_at', 'request__event__name')
    search_fields = ('matched_user__username', 'request__user__username', 'request__event__name')
    readonly_fields = ('matched_at', 'updated_at')
    ordering = ('-matched_at',)
    date_hierarchy = 'matched_at'
    
    fieldsets = (
        ('匹配信息', {
            'fields': ('request', 'matched_user', 'status')
        }),
        ('时间信息', {
            'fields': ('matched_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('request__user', 'request__event', 'matched_user')

@admin.register(UserFeedback)
class UserFeedbackAdmin(admin.ModelAdmin):
    list_display = ('__str__', 'from_user', 'to_user', 'rating', 'created_at')
    list_filter = ('rating', 'created_at')
    search_fields = ('from_user__username', 'to_user__username', 'comment')
    readonly_fields = ('created_at',)
    ordering = ('-created_at',)
    date_hierarchy = 'created_at'
    
    fieldsets = (
        ('反馈信息', {
            'fields': ('from_user', 'to_user', 'rating')
        }),
        ('评价内容', {
            'fields': ('comment',)
        }),
        ('时间信息', {
            'fields': ('created_at',),
            'classes': ('collapse',)
        })
    )
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('from_user', 'to_user')
