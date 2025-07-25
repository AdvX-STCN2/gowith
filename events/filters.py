import django_filters
from django.db.models import Q
from .models import Event


class EventFilter(django_filters.FilterSet):
    """活动过滤器"""
    
    city = django_filters.CharFilter(
        field_name='location__city',
        lookup_expr='icontains',
        help_text='按城市过滤'
    )
    
    date = django_filters.DateFilter(
        field_name='start_time__date',
        help_text='按日期过滤（YYYY-MM-DD格式）'
    )
    
    date_from = django_filters.DateFilter(
        field_name='start_time__date',
        lookup_expr='gte',
        help_text='开始日期（从此日期开始）'
    )
    
    date_to = django_filters.DateFilter(
        field_name='start_time__date',
        lookup_expr='lte',
        help_text='结束日期（到此日期结束）'
    )
    
    is_online = django_filters.BooleanFilter(
        field_name='is_online',
        help_text='是否为线上活动'
    )
    
    creator = django_filters.NumberFilter(
        field_name='creator__id',
        help_text='按创建者ID过滤'
    )
    
    class Meta:
        model = Event
        fields = ['city', 'date', 'date_from', 'date_to', 'is_online', 'creator']