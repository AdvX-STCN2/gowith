import json
from django.shortcuts import render, redirect
from django.http import JsonResponse
from django.contrib.auth import login, logout
from django.contrib.auth.models import User
from django.views.decorators.csrf import csrf_exempt
from django.conf import settings
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from casdoor import CasdoorSDK
import urllib.parse

# 初始化CasDoor SDK
def get_casdoor_sdk():
    return CasdoorSDK(
        endpoint=settings.CASDOOR_ENDPOINT,
        client_id=settings.CASDOOR_CLIENT_ID,
        client_secret=settings.CASDOOR_CLIENT_SECRET,
        certificate=settings.CASDOOR_CERTIFICATE,
        org_name=settings.CASDOOR_ORGANIZATION_NAME,
        app_name=settings.CASDOOR_APPLICATION_NAME,
    )

@api_view(['GET'])
@permission_classes([AllowAny])
def casdoor_login(request):
    """生成CasDoor登录URL"""
    sdk = get_casdoor_sdk()
    redirect_uri = request.build_absolute_uri('/auth/callback/')
    
    # 生成登录URL
    login_url = sdk.get_auth_link(redirect_uri)
    
    return Response({
        'login_url': login_url,
        'message': '请访问此URL进行登录'
    })

@api_view(['GET'])
@permission_classes([AllowAny])
def casdoor_callback(request):
    """处理CasDoor回调"""
    code = request.GET.get('code')
    state = request.GET.get('state')
    
    if not code:
        return Response({'error': '缺少授权码'}, status=400)
    
    try:
        sdk = get_casdoor_sdk()
        
        # 获取访问令牌
        token = sdk.get_oauth_token(code)
        
        if not token:
            return Response({'error': '获取令牌失败'}, status=400)
        
        # 解析用户信息
        user_info = sdk.parse_jwt_token(token)
        
        if not user_info:
            return Response({'error': '解析用户信息失败'}, status=400)
        
        # 获取或创建Django用户
        username = user_info.get('name', user_info.get('sub', ''))
        email = user_info.get('email', '')
        
        user, created = User.objects.get_or_create(
            username=username,
            defaults={
                'email': email,
                'first_name': user_info.get('given_name', ''),
                'last_name': user_info.get('family_name', ''),
            }
        )
        
        # 登录用户
        login(request, user)
        
        # 将token存储在session中
        request.session['casdoor_token'] = token
        request.session['casdoor_user_info'] = user_info
        
        return Response({
            'message': '登录成功',
            'user': {
                'id': user.id,
                'username': user.username,
                'email': user.email,
                'first_name': user.first_name,
                'last_name': user.last_name,
            },
            'token': token
        })
        
    except Exception as e:
        return Response({'error': f'认证失败: {str(e)}'}, status=500)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def casdoor_logout(request):
    """登出用户"""
    # 清除session
    if 'casdoor_token' in request.session:
        del request.session['casdoor_token']
    if 'casdoor_user_info' in request.session:
        del request.session['casdoor_user_info']
    
    # Django登出
    logout(request)
    
    return Response({'message': '登出成功'})

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_user_info(request):
    """获取当前用户信息"""
    user = request.user
    casdoor_user_info = request.session.get('casdoor_user_info', {})
    
    return Response({
        'user': {
            'id': user.id,
            'username': user.username,
            'email': user.email,
            'first_name': user.first_name,
            'last_name': user.last_name,
        },
        'casdoor_info': casdoor_user_info
    })
