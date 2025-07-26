from rest_framework import serializers
from drf_spectacular.utils import extend_schema_field
from drf_spectacular.openapi import OpenApiTypes
from django.contrib.auth import get_user_model
from .models import BuddyRequest, BuddyRequestTag, BuddyMatch, UserFeedback
from profiles.models import UserProfile
from events.models import Event
from authentication.models import Address

User = get_user_model()


class BuddyRequestTagSerializer(serializers.ModelSerializer):
    
    class Meta:
        model = BuddyRequestTag
        fields = ['id', 'tag_name']
        extra_kwargs = {
            'id': {'help_text': '标签ID'},
            'tag_name': {'help_text': '标签名称'}
        }


class BuddyRequestCreateSerializer(serializers.ModelSerializer):
    profile = serializers.PrimaryKeyRelatedField(
        queryset=UserProfile.objects.all(),
        required=False,
        help_text='使用的用户档案ID（不指定则使用主档案）'
    )
    
    class Meta:
        model = BuddyRequest
        fields = [
            'profile', 'event', 'description', 'is_public'
        ]
        extra_kwargs = {
            'profile': {'help_text': '用户档案ID'},
            'event': {'help_text': '活动ID'},
            'description': {'help_text': '搭子请求描述'},
            'is_public': {'help_text': '是否允许别人找搭子'}
        }
    
    def create(self, validated_data):
        user = self.context['request'].user
        validated_data['user'] = user
        if 'profile' not in validated_data or validated_data['profile'] is None:
            primary_profile = user.profiles.filter(is_primary=True).first()
            if not primary_profile:
                raise serializers.ValidationError("用户没有可用的档案，请先创建档案")
            validated_data['profile'] = primary_profile
        
        buddy_request = super().create(validated_data)
        # 标签将由AI后期自动生成，不需要在创建时设置
        return buddy_request
    
    def validate(self, data):
        if 'profile' in data and data['profile'] is not None:
            user = self.context['request'].user
            if data['profile'].user != user:
                raise serializers.ValidationError("只能使用自己的档案")
        
        return data


class BuddyRequestSerializer(serializers.ModelSerializer):
    user_name = serializers.CharField(source='user.username', read_only=True)
    profile_name = serializers.CharField(source='profile.name', read_only=True)
    profile_location = serializers.SerializerMethodField()
    event_name = serializers.CharField(source='event.name', read_only=True)
    tags = BuddyRequestTagSerializer(many=True, read_only=True)
    current_participants = serializers.SerializerMethodField()

    
    class Meta:
        model = BuddyRequest
        fields = [
            'id', 'user', 'user_name', 'profile', 'profile_name', 'profile_location',
            'event', 'event_name', 'description', 
            'current_participants', 
            'is_public', 'tags', 'created_at', 'updated_at'
        ]
        read_only_fields = ['user', 'created_at', 'updated_at']
    
    @extend_schema_field(OpenApiTypes.STR)
    def get_profile_location(self, obj):
        if obj.profile and obj.profile.address:
            return f"{obj.profile.address.city} {obj.profile.address.district}"
        return None
    
    @extend_schema_field(OpenApiTypes.INT)
    def get_current_participants(self, obj):
        return obj.get_current_participants_count()
    



class BuddyRequestListSerializer(serializers.ModelSerializer):
    user_name = serializers.CharField(source='user.username', read_only=True)
    profile_name = serializers.CharField(source='profile.name', read_only=True)
    profile_location = serializers.SerializerMethodField()
    event_name = serializers.CharField(source='event.name', read_only=True)
    tags = BuddyRequestTagSerializer(many=True, read_only=True)
    current_participants = serializers.SerializerMethodField()

    
    class Meta:
        model = BuddyRequest
        fields = [
            'id', 'user_name', 'profile_name', 'profile_location', 'event_name', 
            'description', 'current_participants', 'is_public', 'tags', 'created_at'
        ]
    
    @extend_schema_field(OpenApiTypes.STR)
    def get_profile_location(self, obj):
        if obj.profile and obj.profile.address:
            return f"{obj.profile.address.city} {obj.profile.address.district}"
        return None
    
    @extend_schema_field(OpenApiTypes.INT)
    def get_current_participants(self, obj):
        return obj.get_current_participants_count()
    



class BuddyMatchSerializer(serializers.ModelSerializer):
    matched_user_name = serializers.CharField(source='matched_user.username', read_only=True)
    request_description = serializers.CharField(source='request.description', read_only=True)
    
    class Meta:
        model = BuddyMatch
        fields = [
            'id', 'request', 'request_description',
            'matched_user', 'matched_user_name',
            'status', 'matched_at', 'updated_at'
        ]
        read_only_fields = ['matched_at', 'updated_at']
        extra_kwargs = {
            'id': {'help_text': '匹配ID'},
            'request': {'help_text': '搭子请求ID'},
            'matched_user': {'help_text': '匹配用户ID'},
            'status': {'help_text': '匹配状态'}
        }


class UserFeedbackSerializer(serializers.ModelSerializer):
    from_user_name = serializers.CharField(source='from_user.username', read_only=True)
    to_user_name = serializers.CharField(source='to_user.username', read_only=True)
    
    class Meta:
        model = UserFeedback
        fields = [
            'id', 'from_user', 'from_user_name', 'to_user', 'to_user_name',
            'rating', 'comment', 'created_at'
        ]
        read_only_fields = ['from_user', 'created_at']
        extra_kwargs = {
            'id': {'help_text': '反馈ID'},
            'to_user': {'help_text': '被评价用户ID'},
            'rating': {'help_text': '评分（1-5分）'},
            'comment': {'help_text': '评价内容'}
        }
    
    def create(self, validated_data):
        validated_data['from_user'] = self.context['request'].user
        return super().create(validated_data)
    
    def validate(self, data):
        from_user = self.context['request'].user
        to_user = data['to_user']
        
        if from_user == to_user:
            raise serializers.ValidationError("不能给自己评价")
        if UserFeedback.objects.filter(
            from_user=from_user,
            to_user=to_user
        ).exists():
            raise serializers.ValidationError("已经对该用户进行过评价")
        
        return data


class MatchStatusSerializer(serializers.Serializer):
    request_id = serializers.IntegerField(help_text='搭子请求ID')
    status = serializers.CharField(help_text='处理状态')
    progress = serializers.IntegerField(help_text='处理进度（百分比）')
    message = serializers.CharField(help_text='状态消息', required=False)
    matches = BuddyMatchSerializer(many=True, help_text='匹配结果列表', required=False)
    created_at = serializers.DateTimeField(help_text='创建时间')
    updated_at = serializers.DateTimeField(help_text='更新时间')