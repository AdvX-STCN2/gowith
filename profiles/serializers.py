from rest_framework import serializers
from drf_spectacular.utils import extend_schema_field
from drf_spectacular.types import OpenApiTypes
from .models import UserProfile
from authentication.models import Address
from django.contrib.auth import get_user_model

User = get_user_model()

class ProfileAddressSerializer(serializers.ModelSerializer):
    
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

class UserProfileSerializer(serializers.ModelSerializer):
    user_name = serializers.CharField(
        source='user.username', 
        read_only=True,
        help_text='用户名'
    )
    address_detail = ProfileAddressSerializer(
        source='address', 
        read_only=True,
        help_text='地址详细信息'
    )
    location_display = serializers.SerializerMethodField(
        help_text='地址显示'
    )
    
    class Meta:
        model = UserProfile
        fields = [
            'id', 'user', 'user_name', 'name', 'phone', 'contact_info', 'mbti', 'bio', 
            'avatar_url', 'address', 'address_detail', 'location_display',
            'is_active', 'is_primary', 'created_at', 'updated_at'
        ]
        read_only_fields = ['user', 'created_at', 'updated_at']
        extra_kwargs = {
            'id': {'help_text': '档案ID'},
            'name': {
                'help_text': '档案名称',
                'style': {'placeholder': '请输入档案名称'}
            },
            'phone': {
                'help_text': '联系电话（可选）',
                'style': {'placeholder': '请输入手机号码'}
            },
            'contact_info': {
                'help_text': '联系方式（微信、QQ、邮箱等）',
                'style': {'placeholder': '请输入您的联系方式，如微信号、QQ号等'}
            },
            'mbti': {
                'help_text': 'MBTI性格类型（可选）',
                'style': {'placeholder': '如：ENFP'}
            },
            'bio': {
                'help_text': '个人简介（可选）',
                'style': {'placeholder': '请简单介绍一下自己...'}
            },
            'avatar_url': {
                'help_text': '头像URL（可选）',
                'style': {'placeholder': 'https://example.com/avatar.jpg'}
            },
            'address': {'help_text': '地址ID'},
            'is_active': {'help_text': '是否激活'},
            'is_primary': {'help_text': '是否为主档案'}
        }
    
    @extend_schema_field(OpenApiTypes.STR)
    def get_location_display(self, obj):
        return obj.get_location_display()

class UserProfileListSerializer(serializers.ModelSerializer):
    location_display = serializers.SerializerMethodField(
        help_text='地址显示'
    )
    
    class Meta:
        model = UserProfile
        fields = [
            'id', 'name', 'mbti', 'avatar_url', 'location_display',
            'is_active', 'is_primary', 'created_at'
        ]
    
    @extend_schema_field(OpenApiTypes.STR)
    def get_location_display(self, obj):
        return obj.get_location_display()

class UserProfileCreateSerializer(serializers.ModelSerializer):
    address_data = ProfileAddressSerializer(write_only=True, required=False, help_text='地址信息')
    
    class Meta:
        model = UserProfile
        fields = [
            'name', 'phone', 'contact_info', 'mbti', 'bio', 'avatar_url', 
            'address', 'address_data', 'is_primary'
        ]
        extra_kwargs = {
            'name': {
                'help_text': '档案名称',
                'style': {'placeholder': '请输入档案名称'}
            },
            'phone': {
                'help_text': '联系电话（可选）',
                'style': {'placeholder': '请输入手机号码'}
            },
            'contact_info': {
                'help_text': '联系方式（微信、QQ、邮箱等）',
                'style': {'placeholder': '请输入您的联系方式，如微信号、QQ号等'}
            },
            'mbti': {
                'help_text': 'MBTI性格类型（可选）',
                'style': {'placeholder': '如：ENFP'}
            },
            'bio': {
                'help_text': '个人简介（可选）',
                'style': {'placeholder': '请简单介绍一下自己...'}
            },
            'avatar_url': {
                'help_text': '头像URL（可选）',
                'style': {'placeholder': 'https://example.com/avatar.jpg'}
            },
            'address': {'help_text': '地址ID（可选，与address_data二选一）'},
            'is_primary': {'help_text': '是否为主档案'}
        }
    
    def create(self, validated_data):
        address_data = validated_data.pop('address_data', None)
        user = self.context['request'].user
        
        if address_data:
            profile, address, created = UserProfile.create_with_address(
                user=user,
                address_data=address_data,
                **validated_data
            )
        else:
            profile = UserProfile.objects.create(
                user=user,
                **validated_data
            )
        
        return profile