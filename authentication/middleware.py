import logging
import jwt
from django.utils.deprecation import MiddlewareMixin
from django.contrib.auth import logout
from django.http import JsonResponse
from .casdoor_config import CasdoorConfig
from .casdoor_utils import CasdoorUtils

logger = logging.getLogger(__name__)


class CasdoorTokenMiddleware(MiddlewareMixin):
    """Casdoor Token中间件
    
    功能：
    1. 自动验证token有效性
    2. 自动刷新即将过期的token
    3. 处理token过期的情况
    """
    
    def __init__(self, get_response):
        self.get_response = get_response
        super().__init__(get_response)
    
    def process_request(self, request):
        """处理请求"""
        # 跳过不需要认证的路径
        if self._should_skip_auth(request):
            return None
        
        # 检查用户是否已登录
        if not request.user.is_authenticated:
            return None
        
        # 检查是否有Casdoor token
        access_token = request.session.get('casdoor_access_token')
        if not access_token:
            return None
        
        # 验证token有效性
        if not self._validate_token(request, access_token):
            # Token无效，尝试刷新
            if not CasdoorUtils.refresh_token_if_needed(request):
                # 刷新失败，清除会话并登出
                self._logout_user(request)
                return JsonResponse({
                    'status': 'error',
                    'message': 'Token已过期，请重新登录',
                    'code': 'TOKEN_EXPIRED'
                }, status=401)
        
        return None
    
    def _should_skip_auth(self, request) -> bool:
        """判断是否应该跳过认证检查"""
        skip_paths = [
            '/auth/login/',
            '/auth/callback/',
            '/admin/',
            '/static/',
            '/media/',
        ]
        
        path = request.path
        return any(path.startswith(skip_path) for skip_path in skip_paths)
    
    def _validate_token(self, request, access_token: str) -> bool:
        """验证token有效性"""
        try:
            sdk = CasdoorConfig.get_sdk()
            user_info = sdk.parse_jwt_token(access_token)
            
            # 更新会话中的用户信息
            request.session['casdoor_user'] = user_info
            return True
            
        except jwt.ExpiredSignatureError:
            logger.info("Token已过期")
            return False
        except jwt.InvalidTokenError as e:
            logger.warning(f"Token无效: {e}")
            return False
        except Exception as e:
            logger.error(f"Token验证失败: {e}")
            return False
    
    def _logout_user(self, request):
        """登出用户"""
        CasdoorUtils.clear_user_session(request)
        logout(request)


class CasdoorCORSMiddleware(MiddlewareMixin):
    """Casdoor CORS中间件
    
    处理跨域请求，特别是与Casdoor前端的交互
    """
    
    def process_response(self, request, response):
        """处理响应，添加CORS头"""
        # 只对API请求添加CORS头
        if request.path.startswith('/auth/') or request.path.startswith('/api/'):
            response['Access-Control-Allow-Origin'] = '*'
            response['Access-Control-Allow-Methods'] = 'GET, POST, PUT, DELETE, OPTIONS'
            response['Access-Control-Allow-Headers'] = 'Content-Type, Authorization, X-Requested-With'
            response['Access-Control-Allow-Credentials'] = 'true'
        
        return response
    
    def process_request(self, request):
        """处理预检请求"""
        if request.method == 'OPTIONS':
            response = JsonResponse({'status': 'ok'})
            response['Access-Control-Allow-Origin'] = '*'
            response['Access-Control-Allow-Methods'] = 'GET, POST, PUT, DELETE, OPTIONS'
            response['Access-Control-Allow-Headers'] = 'Content-Type, Authorization, X-Requested-With'
            response['Access-Control-Allow-Credentials'] = 'true'
            return response
        
        return None