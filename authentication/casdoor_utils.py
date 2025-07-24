import json
import logging
from typing import Dict, Tuple, Optional, Any
from functools import wraps
from django.http import JsonResponse
from django.contrib.auth.models import User
from django.contrib.auth import login as django_login
from .casdoor_config import CasdoorConfig

logger = logging.getLogger(__name__)


class CasdoorUtils:
    """Casdoor工具类"""
    
    @staticmethod
    def parse_error(response_data: Any) -> Tuple[Optional[str], Optional[str]]:
        """解析错误信息"""
        if isinstance(response_data, dict):
            error = response_data.get('error')
            error_description = response_data.get('error_description')
            return error, error_description
        
        if isinstance(response_data, str):
            try:
                data = json.loads(response_data)
                error = data.get('error')
                error_description = data.get('error_description')
                return error, error_description
            except json.JSONDecodeError:
                return "JSONDecodeError", f"输入不是有效的JSON: {response_data}"
        
        return None, None
    
    @staticmethod
    def get_or_create_user(user_info: Dict) -> Tuple[User, bool]:
        """根据Casdoor用户信息获取或创建Django用户"""
        username = user_info.get('name', user_info.get('sub', ''))
        email = user_info.get('email', '')
        
        # 尝试通过用户名查找用户
        try:
            user = User.objects.get(username=username)
            created = False
            
            # 更新用户信息
            user.email = email
            user.first_name = user_info.get('given_name', user_info.get('firstName', ''))
            user.last_name = user_info.get('family_name', user_info.get('lastName', ''))
            user.save()
            
        except User.DoesNotExist:
            # 创建新用户
            user = User.objects.create_user(
                username=username,
                email=email,
                first_name=user_info.get('given_name', user_info.get('firstName', '')),
                last_name=user_info.get('family_name', user_info.get('lastName', '')),
            )
            created = True
        
        return user, created
    
    @staticmethod
    def store_user_session(request, user_info: Dict, token: Dict):
        """存储用户会话信息"""
        request.session['casdoor_user'] = user_info
        request.session['casdoor_token'] = token
        request.session['casdoor_access_token'] = token.get('access_token')
        request.session['casdoor_refresh_token'] = token.get('refresh_token')
    
    @staticmethod
    def clear_user_session(request):
        """清除用户会话信息"""
        session_keys = [
            'casdoor_user',
            'casdoor_token', 
            'casdoor_access_token',
            'casdoor_refresh_token'
        ]
        
        for key in session_keys:
            if key in request.session:
                del request.session[key]
    
    @staticmethod
    def is_authenticated(request) -> bool:
        """检查用户是否已认证"""
        return (
            request.user.is_authenticated and 
            'casdoor_user' in request.session and
            'casdoor_access_token' in request.session
        )
    
    @staticmethod
    def get_user_info_from_session(request) -> Optional[Dict]:
        """从会话中获取用户信息"""
        return request.session.get('casdoor_user')
    
    @staticmethod
    def refresh_token_if_needed(request) -> bool:
        """如果需要，刷新token"""
        refresh_token = request.session.get('casdoor_refresh_token')
        if not refresh_token:
            return False
        
        try:
            sdk = CasdoorConfig.get_sdk()
            new_token = sdk.refresh_oauth_tokens(refresh_token)
            
            if new_token and 'access_token' in new_token:
                request.session['casdoor_token'] = new_token
                request.session['casdoor_access_token'] = new_token.get('access_token')
                if 'refresh_token' in new_token:
                    request.session['casdoor_refresh_token'] = new_token.get('refresh_token')
                return True
        except Exception as e:
            logger.error(f"刷新token失败: {e}")
        
        return False


def casdoor_login_required(view_func):
    """Casdoor登录装饰器"""
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not CasdoorUtils.is_authenticated(request):
            return JsonResponse({
                'status': 'error',
                'message': '用户未登录',
                'code': 'UNAUTHORIZED'
            }, status=401)
        
        return view_func(request, *args, **kwargs)
    
    return wrapper


def casdoor_permission_required(permission_model: str, sub: str, obj: str, act: str):
    """Casdoor权限检查装饰器"""
    def decorator(view_func):
        @wraps(view_func)
        def wrapper(request, *args, **kwargs):
            if not CasdoorUtils.is_authenticated(request):
                return JsonResponse({
                    'status': 'error',
                    'message': '用户未登录',
                    'code': 'UNAUTHORIZED'
                }, status=401)
            
            try:
                sdk = CasdoorConfig.get_sdk()
                user_info = CasdoorUtils.get_user_info_from_session(request)
                
                # 动态替换权限参数中的用户信息
                actual_sub = sub.replace('{username}', user_info.get('name', ''))
                
                has_permission = sdk.enforce(
                    permission_model_name=permission_model,
                    sub=actual_sub,
                    obj=obj,
                    act=act
                )
                
                if not has_permission:
                    return JsonResponse({
                        'status': 'error',
                        'message': '权限不足',
                        'code': 'FORBIDDEN'
                    }, status=403)
                
            except Exception as e:
                logger.error(f"权限检查失败: {e}")
                return JsonResponse({
                    'status': 'error',
                    'message': '权限检查失败',
                    'code': 'PERMISSION_CHECK_ERROR'
                }, status=500)
            
            return view_func(request, *args, **kwargs)
        
        return wrapper
    return decorator