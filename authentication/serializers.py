from rest_framework import serializers
from django.contrib.auth.models import User


class CasdoorCallbackSerializer(serializers.Serializer):
    code = serializers.CharField(
        help_text='OAuth2授权码',
        required=True
    )
    state = serializers.CharField(
        help_text='状态参数',
        required=False,
        allow_blank=True
    )


class LogoutResponseSerializer(serializers.Serializer):
    status = serializers.CharField(help_text='响应状态')
    message = serializers.CharField(help_text='响应消息')


class RefreshTokenResponseSerializer(serializers.Serializer):
    status = serializers.CharField(help_text='响应状态')
    message = serializers.CharField(help_text='响应消息')
    access_token = serializers.CharField(
        help_text='访问令牌',
        required=False
    )


class UserInfoSerializer(serializers.ModelSerializer):
    date_joined = serializers.DateTimeField(
        format='%Y-%m-%dT%H:%M:%S.%fZ',
        read_only=True
    )
    last_login = serializers.DateTimeField(
        format='%Y-%m-%dT%H:%M:%S.%fZ',
        read_only=True,
        allow_null=True
    )
    
    class Meta:
        model = User
        fields = [
            'id', 'username', 'email', 'first_name', 'last_name',
            'is_staff', 'is_superuser', 'date_joined', 'last_login'
        ]
        read_only_fields = fields


class AuthStatusResponseSerializer(serializers.Serializer):
    status = serializers.CharField(help_text='响应状态')
    authenticated = serializers.BooleanField(help_text='是否已认证')
    user = UserInfoSerializer(
        help_text='用户信息',
        required=False
    )


class ErrorResponseSerializer(serializers.Serializer):
    status = serializers.CharField(help_text='响应状态')
    message = serializers.CharField(help_text='错误消息')
    code = serializers.CharField(
        help_text='错误代码',
        required=False
    )