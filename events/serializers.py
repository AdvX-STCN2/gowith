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
            'id', 'user_name', 'description', 
            'current_participants', 'is_public', 'created_at'
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
            'is_online', 'logo_url', 'banner_url', 'introduction', 'description', 'creator',
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
            },
            'description': {
                'help_text': '文字描述（可选）',
                'style': {'placeholder': '请输入活动的详细文字描述...'}
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
    location_address = serializers.SerializerMethodField(
        help_text='活动完整地址'
    )
    participant_count = serializers.SerializerMethodField(
        help_text='参与者数量'
    )
    
    class Meta:
        model = Event
        fields = [
            'id', 'name', 'start_time', 'end_time', 'location_address',
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
    
    @extend_schema_field(OpenApiTypes.STR)
    def get_location_address(self, obj):
        if obj.location:
            return obj.location.get_full_address()
        return None
    
    @extend_schema_field(OpenApiTypes.INT)
    def get_participant_count(self, obj):
        return obj.get_participant_count()

class EventCreateSerializer(serializers.ModelSerializer):
    location_data = AddressSerializer(required=False, help_text='新建地点信息（可选，如果提供则会创建新地点）')
    
    class Meta:
        model = Event
        fields = [
            'id', 'name', 'start_time', 'end_time', 'location', 'location_data',
            'is_online', 'logo_url', 'banner_url', 'introduction', 'description'
        ]
        extra_kwargs = {
            'name': {
                'help_text': '活动名称',
                'style': {'placeholder': '请输入活动名称，如：AdventureX 2024春季活动'}
            },
            'start_time': {'help_text': '活动开始时间'},
            'end_time': {'help_text': '活动结束时间'},
            'location': {'help_text': '活动地点ID（如果是线下活动，与location_data二选一）', 'required': False},
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
            },
            'description': {
                'help_text': '文字描述（可选）',
                'style': {'placeholder': '请输入活动的详细文字描述...'},
                'required': False
            }
        }
    
    def create(self, validated_data):
        location_data = validated_data.pop('location_data', None)
        validated_data['creator'] = self.context['request'].user
        
        # 如果提供了location_data，创建新地点
        if location_data:
            address, created = Address.get_or_create_address(
                country=location_data.get('country', '中国'),
                province=location_data['province'],
                city=location_data['city'],
                district=location_data.get('district'),
                detailed_address=location_data.get('detailed_address'),
                latitude=location_data.get('latitude'),
                longitude=location_data.get('longitude')
            )
            validated_data['location'] = address
        
        return super().create(validated_data)
    
    def validate(self, data):
        if data['start_time'] >= data['end_time']:
            raise serializers.ValidationError("活动开始时间必须早于结束时间")
        
        location = data.get('location')
        location_data = data.get('location_data')
        is_online = data.get('is_online', False)
        
        if not is_online:
            if not location and not location_data:
                raise serializers.ValidationError("线下活动必须指定地点（location）或提供新地点信息（location_data）")
            
            if location and location_data:
                raise serializers.ValidationError("不能同时指定现有地点（location）和新地点信息（location_data）")
            
            # 如果提供了location_data，验证必需字段
            if location_data:
                if not location_data.get('province') or not location_data.get('city'):
                    raise serializers.ValidationError("新建地点必须包含省份和城市信息")
        
        return data