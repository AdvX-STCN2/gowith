import logging
from django.http import JsonResponse
from django.contrib.auth import login as django_login, logout as django_logout
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.views import View
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from rest_framework import status
from rest_framework.views import APIView
from rest_framework.generics import GenericAPIView
from drf_spectacular.utils import extend_schema, OpenApiResponse
from drf_spectacular.types import OpenApiTypes

from .casdoor_config import CasdoorConfig
from .casdoor_utils import CasdoorUtils, casdoor_login_required
from .serializers import (
    CasdoorCallbackSerializer,
    LogoutResponseSerializer,
    RefreshTokenResponseSerializer,
    AuthStatusResponseSerializer,
    ErrorResponseSerializer
)

logger = logging.getLogger(__name__)

@extend_schema(
    summary="获取Casdoor登录URL",
    description="""生成Casdoor单点登录的授权URL。
    
    **功能说明：**
    - 生成OAuth2授权链接
    - 用户访问此URL进行第三方登录
    - 无需认证即可调用
    """,
    responses={
        200: OpenApiResponse(
            response={
                'type': 'object',
                'properties': {
                    'status': {'type': 'string', 'example': 'ok'},
                    'login_url': {'type': 'string', 'example': 'https://casdoor.example.com/login/oauth/authorize?...'},
                    'message': {'type': 'string', 'example': '请访问此URL进行登录'}
                }
            },
            description="成功生成登录URL"
        ),
        500: OpenApiResponse(
            response={
                'type': 'object',
                'properties': {
                    'status': {'type': 'string', 'example': 'error'},
                    'message': {'type': 'string'},
                    'code': {'type': 'string', 'example': 'LOGIN_URL_GENERATION_ERROR'}
                }
            },
            description="生成登录URL失败"
        )
    },
    tags=['用户认证']
)
@api_view(['GET'])
@permission_classes([AllowAny])
def casdoor_login(request):
    """生成Casdoor登录URL"""
    try:
        sdk = CasdoorConfig.get_sdk()
        redirect_uri = CasdoorConfig.get_redirect_uri(request)
        
        # 生成登录URL
        login_url = sdk.get_auth_link(
            redirect_uri=redirect_uri,
            response_type='code',
            scope='read'
        )
        
        logger.info(f"生成登录URL: {login_url}")
        
        return Response({
            'status': 'ok',
            'login_url': login_url,
            'message': '请访问此URL进行登录'
        }, status=status.HTTP_200_OK)
        
    except Exception as e:
        logger.error(f"生成登录URL失败: {e}")
        return Response({
            'status': 'error',
            'message': f'生成登录URL失败: {str(e)}',
            'code': 'LOGIN_URL_GENERATION_ERROR'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@extend_schema(
    summary="Casdoor OAuth回调处理",
    description="""处理Casdoor OAuth2授权回调。
    
    **功能说明：**
    - 接收OAuth2授权码
    - 获取访问令牌和用户信息
    - 创建或更新Django用户
    - 自动登录用户
    - 重定向到前端页面
    
    **注意：** 此接口通常由Casdoor服务器调用，不需要手动调用
    """,
    request=CasdoorCallbackSerializer,
    responses={
        302: OpenApiResponse(description="重定向到前端成功/错误页面"),
        500: OpenApiResponse(description="服务器内部错误")
    },
    tags=['用户认证']
)
@api_view(['GET', 'POST'])
@permission_classes([AllowAny])
def casdoor_callback(request):
    """处理Casdoor回调"""
    # 支持GET和POST两种方式获取参数
    if request.method == 'GET':
        code = request.GET.get('code')
        state = request.GET.get('state')
    else:
        code = request.data.get('code')
        state = request.data.get('state')
    
    if not code:
        logger.error("OAuth回调缺少授权码")
        

        frontend_url = CasdoorConfig.get_frontend_endpoint()
        error_url = f"{frontend_url}/auth/error?message=缺少授权码"
        
        from django.shortcuts import redirect
        return redirect(error_url)
    
    try:
        sdk = CasdoorConfig.get_sdk()
        
        # 获取访问令牌
        token_response = sdk.get_oauth_token(code)
        
        # 检查token响应是否有错误
        error, error_description = CasdoorUtils.parse_error(token_response)
        if error:
            logger.error(f"获取token失败: {error} - {error_description}")
            
            # 重定向到前端错误页面
            frontend_url = CasdoorConfig.get_frontend_endpoint()
            error_url = f"{frontend_url}/auth/error?message={error_description or error}"
            
            from django.shortcuts import redirect
            return redirect(error_url)
        
        if not token_response or 'access_token' not in token_response:
            logger.error("Token响应格式错误")
            
            # 重定向到前端错误页面
            frontend_url = CasdoorConfig.get_frontend_endpoint()
            error_url = f"{frontend_url}/auth/error?message=获取令牌失败"
            
            from django.shortcuts import redirect
            return redirect(error_url)
        
        # 解析用户信息
        access_token = token_response['access_token']
        user_info = sdk.parse_jwt_token(access_token)
        
        if not user_info:
            logger.error("解析用户信息失败")
            
            # 重定向到前端错误页面
            frontend_url = CasdoorConfig.get_frontend_endpoint()
            error_url = f"{frontend_url}/auth/error?message=解析用户信息失败"
            
            from django.shortcuts import redirect
            return redirect(error_url)
        
        # 获取或创建Django用户
        user, created = CasdoorUtils.get_or_create_user(user_info)
        
        # 登录用户
        django_login(request, user)
        
        # 存储用户会话信息
        CasdoorUtils.store_user_session(request, user_info, token_response)
        
        logger.info(f"用户 {user.username} 登录成功 (创建新用户: {created})")
        
        # 获取前端重定向URL
        frontend_url = CasdoorConfig.get_frontend_endpoint()
        redirect_url = f"{frontend_url}/auth/success"
        
        # 重定向到前端
        from django.shortcuts import redirect
        return redirect(redirect_url)
        
    except Exception as e:
        logger.error(f"认证回调失败: {e}")
        
        # 重定向到前端错误页面
        frontend_url = CasdoorConfig.get_frontend_endpoint()
        error_url = f"{frontend_url}/auth/error?message={str(e)}"
        
        from django.shortcuts import redirect
        return redirect(error_url)

@extend_schema(
    summary="用户登出",
    description="""登出当前用户并清除会话信息。
    
    **功能说明：**
    - 清除Casdoor会话信息
    - 执行Django登出操作
    - 允许未认证用户调用
    """,
    responses={
        200: OpenApiResponse(
            response=LogoutResponseSerializer,
            description="登出成功"
        ),
        500: OpenApiResponse(
            response=ErrorResponseSerializer,
            description="登出失败"
        )
    },
    tags=['用户认证']
)
class CasdoorLogoutView(GenericAPIView):
    permission_classes = [AllowAny]
    serializer_class = LogoutResponseSerializer
    
    def post(self, request):
        try:
            CasdoorUtils.clear_user_session(request)
            if request.user.is_authenticated:
                username = request.user.username
                django_logout(request)
                logger.info(f"用户 {username} 登出成功")
            
            return Response({
                'status': 'ok',
                'message': '登出成功'
            }, status=status.HTTP_200_OK)
            
        except Exception as e:
            logger.error(f"登出失败: {e}")
            return Response({
                'status': 'error',
                'message': f'登出失败: {str(e)}',
                'code': 'LOGOUT_ERROR'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)



casdoor_logout = CasdoorLogoutView.as_view()

@extend_schema(
    summary="获取当前用户信息",
    description="""获取当前登录用户的详细信息。
    
    **权限要求：** 需要通过Casdoor认证
    **返回信息：** 包含Django用户信息和Casdoor用户信息
    """,
    responses={
        200: OpenApiResponse(
            response={
                'type': 'object',
                'properties': {
                    'status': {'type': 'string', 'example': 'ok'},
                    'user': {
                        'type': 'object',
                        'properties': {
                            'id': {'type': 'integer'},
                            'username': {'type': 'string'},
                            'email': {'type': 'string'},
                            'first_name': {'type': 'string'},
                            'last_name': {'type': 'string'},
                            'is_staff': {'type': 'boolean'},
                            'is_superuser': {'type': 'boolean'},
                            'date_joined': {'type': 'string', 'format': 'date-time'},
                            'last_login': {'type': 'string', 'format': 'date-time'}
                        }
                    },
                    'casdoor_info': {'type': 'object', 'description': 'Casdoor用户信息'}
                }
            },
            description="成功返回用户信息"
        ),
        401: OpenApiResponse(description="未认证"),
        500: OpenApiResponse(
            response={
                'type': 'object',
                'properties': {
                    'status': {'type': 'string', 'example': 'error'},
                    'message': {'type': 'string'},
                    'code': {'type': 'string', 'example': 'USER_INFO_ERROR'}
                }
            },
            description="获取用户信息失败"
        )
    },
    tags=['用户认证']
)
@api_view(['GET'])
@casdoor_login_required
def get_user_info(request):
    try:
        user = request.user
        casdoor_user_info = CasdoorUtils.get_user_info_from_session(request)
        
        return Response({
            'status': 'ok',
            'user': {
                'id': user.id,
                'username': user.username,
                'email': user.email,
                'first_name': user.first_name,
                'last_name': user.last_name,
                'is_staff': user.is_staff,
                'is_superuser': user.is_superuser,
                'date_joined': user.date_joined.isoformat() if user.date_joined else None,
                'last_login': user.last_login.isoformat() if user.last_login else None,
            },
            'casdoor_info': casdoor_user_info or {}
        }, status=status.HTTP_200_OK)
        
    except Exception as e:
        logger.error(f"获取用户信息失败: {e}")
        return Response({
            'status': 'error',
            'message': f'获取用户信息失败: {str(e)}',
            'code': 'USER_INFO_ERROR'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@extend_schema(
    summary="刷新访问令牌",
    description="""刷新Casdoor访问令牌。
    
    **权限要求：** 需要通过Casdoor认证
    **功能说明：** 检查并刷新过期的访问令牌
    """,
    responses={
        200: OpenApiResponse(
            response=RefreshTokenResponseSerializer,
            description="Token刷新成功"
        ),
        400: OpenApiResponse(
            response=ErrorResponseSerializer,
            description="Token刷新失败"
        ),
        500: OpenApiResponse(
            response=ErrorResponseSerializer,
            description="服务器内部错误"
        )
    },
    tags=['用户认证']
)
class RefreshTokenView(GenericAPIView):
    serializer_class = RefreshTokenResponseSerializer
    
    @casdoor_login_required
    def post(self, request):
        try:
            if CasdoorUtils.refresh_token_if_needed(request):
                return Response({
                    'status': 'ok',
                    'message': 'Token刷新成功',
                    'access_token': request.session.get('casdoor_access_token')
                }, status=status.HTTP_200_OK)
            else:
                return Response({
                    'status': 'error',
                    'message': 'Token刷新失败',
                    'code': 'TOKEN_REFRESH_ERROR'
                }, status=status.HTTP_400_BAD_REQUEST)
                
        except Exception as e:
            logger.error(f"刷新token失败: {e}")
            return Response({
                'status': 'error',
                'message': f'刷新token失败: {str(e)}',
                'code': 'TOKEN_REFRESH_ERROR'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# 为了保持向后兼容性，保留函数视图的别名
refresh_token = RefreshTokenView.as_view()


@extend_schema(
    summary="检查认证状态",
    description="""检查当前用户的认证状态。
    
    **功能说明：**
    - 检查用户是否已通过Casdoor认证
    - 返回基本用户信息（如果已认证）
    - 允许未认证用户调用
    """,
    responses={
        200: OpenApiResponse(
            response=AuthStatusResponseSerializer,
            description="成功返回认证状态"
        ),
        500: OpenApiResponse(
            response=ErrorResponseSerializer,
            description="检查认证状态失败"
        )
    },
    tags=['用户认证']
)
@api_view(['GET'])
@permission_classes([AllowAny])
def auth_status(request):
    try:
        is_authenticated = CasdoorUtils.is_authenticated(request)
        
        response_data = {
            'status': 'ok',
            'authenticated': is_authenticated
        }
        
        if is_authenticated:
            user = request.user
            response_data['user'] = {
                'id': user.id,
                'username': user.username,
                'email': user.email
            }
        
        return Response(response_data, status=status.HTTP_200_OK)
        
    except Exception as e:
        logger.error(f"检查认证状态失败: {e}")
        return Response({
            'status': 'error',
            'message': f'检查认证状态失败: {str(e)}',
            'code': 'AUTH_STATUS_ERROR'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
