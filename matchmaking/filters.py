import django_filters
from django.db.models import Q
from .models import BuddyRequest


class BuddyRequestFilter(django_filters.FilterSet):
    """搭子请求过滤器"""
    
    activity_type = django_filters.CharFilter(
        field_name='event__activity_type',
        lookup_expr='icontains',
        help_text='按活动类型过滤'
    )
    
    status = django_filters.ChoiceFilter(
        field_name='status',
        choices=BuddyRequest.STATUS_CHOICES,
        help_text='按状态过滤'
    )
    
    event = django_filters.NumberFilter(
        field_name='event__id',
        help_text='按活动ID过滤'
    )
    
    city = django_filters.CharFilter(
        field_name='event__location__city',
        lookup_expr='icontains',
        help_text='按城市过滤'
    )
    
    start_date = django_filters.DateFilter(
        field_name='event__start_time__date',
        lookup_expr='gte',
        help_text='开始日期（从此日期开始）'
    )
    
    end_date = django_filters.DateFilter(
        field_name='event__end_time__date',
        lookup_expr='lte',
        help_text='结束日期（到此日期结束）'
    )
    

    
    has_space = django_filters.BooleanFilter(
        method='filter_has_space',
        help_text='是否还有空位'
    )
    
    tags = django_filters.CharFilter(
        method='filter_by_tags',
        help_text='按标签过滤（标签名称，支持多个，用逗号分隔）'
    )
    
    user = django_filters.NumberFilter(
        field_name='user__id',
        help_text='按用户ID过滤'
    )
    
    profile = django_filters.NumberFilter(
        field_name='profile__id',
        help_text='按档案ID过滤'
    )
    
    def filter_has_space(self, queryset, name, value):
        """过滤是否还有空位"""
        if value is True:
            # 返回还有空位的请求
            return queryset.filter(
                status='open'
            )
        elif value is False:
            # 返回已满员的请求
            return queryset.none()
        return queryset
    
    def filter_by_tags(self, queryset, name, value):
        """按标签过滤"""
        if value:
            tag_names = [tag.strip() for tag in value.split(',')]
            return queryset.filter(
                tags__name__in=tag_names
            ).distinct()
        return queryset
    
    class Meta:
        model = BuddyRequest
        fields = [
            'activity_type', 'status', 'event', 'city',
            'start_date', 'end_date',
            'has_space', 'tags', 'user', 'profile'
        ]