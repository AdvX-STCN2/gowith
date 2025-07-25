from rest_framework import serializers
from drf_spectacular.utils import extend_schema_field
from drf_spectacular.types import OpenApiTypes
from .models import Event
from authentication.models import Address
from matchmaking.models import BuddyRequest
from django.contrib.auth import get_user_model

User = get_user_model()

class AddressSerializer(serializers.ModelSerializer):
    
    class Meta:
        model = Address
        fields = ['id', 'country', 'province', 'city', 'district', 'detailed_address', 'latitude', 'longitude']
        extra_kwargs = {
            'id': {'help_text': '地址ID'},
            'country': {'help_text': '国家'},
            'province': {'help_text': '省份/州'},
            'city': {'help_text': '城市'},
            'district': {'help_text': '区/县'},
            'detailed_address': {'help_text': '详细地址'},
            'latitude': {'help_text': '纬度'},
            'longitude': {'help_text': '经度'}
        }

class BuddyRequestSimpleSerializer(serializers.ModelSerializer):
    user_name = serializers.CharField(source='user.username', read_only=True)
    current_participants = serializers.SerializerMethodField()
    
    class Meta:
        model = BuddyRequest
        fields = [
            'id', 'user_name', 'activity_type', 'description', 
            'start_time', 'end_time', 'max_participants', 
            'current_participants', 'status', 'created_at'
        ]
    
    @extend_schema_field(OpenApiTypes.INT)
    def get_current_participants(self, obj):
        return obj.get_current_participants_count()

class EventSerializer(serializers.ModelSerializer):
    creator_name = serializers.CharField(
        source='creator.username', 
        read_only=True,
        help_text='活动创建者用户名'
    )
    location_detail = AddressSerializer(
        source='location', 
        read_only=True,
        help_text='活动地点详细信息'
    )
    participant_count = serializers.SerializerMethodField(
        help_text='参与者数量（基于搭子请求）'
    )
    buddy_requests = BuddyRequestSimpleSerializer(
        many=True,
        read_only=True,
        help_text='该活动的搭子请求列表'
    )
    
    class Meta:
        model = Event
        fields = [
            'id', 'name', 'start_time', 'end_time', 'location', 'location_detail',
            'is_online', 'logo_url', 'banner_url', 'introduction', 'creator',
            'creator_name', 'participant_count', 'buddy_requests', 'created_at'
        ]
        read_only_fields = ['creator', 'created_at']
        extra_kwargs = {
            'id': {'help_text': '活动ID'},
            'name': {
                'help_text': '活动名称',
                'style': {'placeholder': '请输入活动名称，如：AdventureX 2024春季活动'}
            },
            'start_time': {'help_text': '活动开始时间'},
            'end_time': {'help_text': '活动结束时间'},
            'location': {'help_text': '活动地点ID（如果是线下活动）'},
            'is_online': {'help_text': '是否为线上活动'},
            'logo_url': {
                'help_text': '活动Logo图片URL（可选）',
                'style': {'placeholder': 'https://example.com/logo.png'}
            },
            'banner_url': {
                'help_text': '活动横幅图片URL（可选）',
                'style': {'placeholder': 'https://example.com/banner.jpg'}
            },
            'introduction': {
                'help_text': '活动介绍和描述（可选）',
                'style': {'placeholder': '请详细介绍这个活动的内容、目标和特色...'}
            }
        }
    
    def create(self, validated_data):
        validated_data['creator'] = self.context['request'].user
        return super().create(validated_data)
    
    @extend_schema_field(OpenApiTypes.INT)
    def get_participant_count(self, obj):
        return obj.get_participant_count()

class EventListSerializer(serializers.ModelSerializer):
    creator_name = serializers.CharField(
        source='creator.username', 
        read_only=True,
        help_text='活动创建者用户名'
    )
    location_city = serializers.CharField(
        source='location.city', 
        read_only=True,
        help_text='活动所在城市'
    )
    participant_count = serializers.SerializerMethodField(
        help_text='参与者数量'
    )
    
    class Meta:
        model = Event
        fields = [
            'id', 'name', 'start_time', 'end_time', 'location_city',
            'is_online', 'logo_url', 'creator_name', 'participant_count', 'created_at'
        ]
        extra_kwargs = {
            'id': {'help_text': '活动ID'},
            'name': {'help_text': '活动名称'},
            'start_time': {'help_text': '活动开始时间'},
            'end_time': {'help_text': '活动结束时间'},
            'is_online': {'help_text': '是否为线上活动'},
            'logo_url': {'help_text': '活动Logo图片URL'},
            'created_at': {'help_text': '创建时间'}
        }
    
    @extend_schema_field(OpenApiTypes.INT)
    def get_participant_count(self, obj):
        return obj.get_participant_count()

class EventCreateSerializer(serializers.ModelSerializer):
    
    class Meta:
        model = Event
        fields = [
            'name', 'start_time', 'end_time', 'location',
            'is_online', 'logo_url', 'banner_url', 'introduction'
        ]
        extra_kwargs = {
            'name': {
                'help_text': '活动名称',
                'style': {'placeholder': '请输入活动名称，如：AdventureX 2024春季活动'}
            },
            'start_time': {'help_text': '活动开始时间'},
            'end_time': {'help_text': '活动结束时间'},
            'location': {'help_text': '活动地点ID（如果是线下活动）', 'required': False},
            'is_online': {'help_text': '是否为线上活动'},
            'logo_url': {
                'help_text': '活动Logo图片URL（可选）',
                'style': {'placeholder': 'https://example.com/logo.png'},
                'required': False
            },
            'banner_url': {
                'help_text': '活动横幅图片URL（可选）',
                'style': {'placeholder': 'https://example.com/banner.jpg'},
                'required': False
            },
            'introduction': {
                'help_text': '活动介绍和描述（可选）',
                'style': {'placeholder': '请详细介绍这个活动的内容、目标和特色...'},
                'required': False
            }
        }
    
    def create(self, validated_data):
        validated_data['creator'] = self.context['request'].user
        return super().create(validated_data)
    
    def validate(self, data):
        if data['start_time'] >= data['end_time']:
            raise serializers.ValidationError("活动开始时间必须早于结束时间")
        
        if not data['is_online'] and not data.get('location'):
            raise serializers.ValidationError("线下活动必须指定地点")
        
        return data