from rest_framework import viewsets, status, permissions
from rest_framework.response import Response
from rest_framework.decorators import action
from django.shortcuts import get_object_or_404
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter, OrderingFilter
from drf_spectacular.utils import extend_schema, extend_schema_view, OpenApiParameter, OpenApiResponse
from drf_spectacular.types import OpenApiTypes
from .models import UserProfile
from .serializers import (
    UserProfileSerializer, 
    UserProfileListSerializer, 
    UserProfileCreateSerializer
)

@extend_schema_view(
    list=extend_schema(
        summary="获取用户档案列表",
        description="""获取当前用户的所有档案列表。
        
        **功能说明：**
        - 仅返回当前登录用户的档案
        - 支持按活跃状态过滤
        - 按创建时间倒序排列
        """,
        parameters=[
            OpenApiParameter(
                name='is_active',
                type=OpenApiTypes.BOOL,
                location=OpenApiParameter.QUERY,
                description='按活跃状态过滤（true=活跃，false=非活跃）'
            )
        ],
        responses={
            200: OpenApiResponse(
                response=UserProfileSerializer(many=True),
                description="成功返回档案列表"
            ),
            401: OpenApiResponse(description="未登录")
        },
        tags=['用户档案']
    ),
    create=extend_schema(
        summary="创建用户档案",
        description="""创建新的用户档案。
        
        **权限要求：** 需要登录
        **自动设置：** 用户为当前登录用户
        **主档案逻辑：** 如果是用户的第一个档案，自动设为主档案
        """,
        request=UserProfileCreateSerializer,
        responses={
            201: OpenApiResponse(
                response=UserProfileSerializer,
                description="档案创建成功"
            ),
            400: OpenApiResponse(description="请求参数错误"),
            401: OpenApiResponse(description="未登录")
        },
        tags=['用户档案']
    ),
    retrieve=extend_schema(
        summary="获取档案详情",
        description="""获取指定档案的详细信息。
        
        **权限要求：** 仅档案所有者可查看
        """,
        responses={
            200: OpenApiResponse(
                response=UserProfileSerializer,
                description="成功返回档案详情"
            ),
            403: OpenApiResponse(description="无权限访问"),
            404: OpenApiResponse(description="档案不存在")
        },
        tags=['用户档案']
    ),
    update=extend_schema(
        summary="更新档案",
        description="""完整更新档案信息。
        
        **权限要求：** 仅档案所有者可操作
        """,
        request=UserProfileCreateSerializer,
        responses={
            200: OpenApiResponse(
                response=UserProfileSerializer,
                description="档案更新成功"
            ),
            400: OpenApiResponse(description="请求参数错误"),
            403: OpenApiResponse(description="无权限操作"),
            404: OpenApiResponse(description="档案不存在")
        },
        tags=['用户档案']
    ),
    partial_update=extend_schema(
        summary="部分更新档案",
        description="""部分更新档案信息。
        
        **权限要求：** 仅档案所有者可操作
        """,
        request=UserProfileCreateSerializer,
        responses={
            200: OpenApiResponse(
                response=UserProfileSerializer,
                description="档案更新成功"
            ),
            400: OpenApiResponse(description="请求参数错误"),
            403: OpenApiResponse(description="无权限操作"),
            404: OpenApiResponse(description="档案不存在")
        },
        tags=['用户档案']
    ),
    destroy=extend_schema(
        summary="删除档案",
        description="""删除档案。
        
        **权限要求：** 仅档案所有者可操作
        **注意：** 无法删除主档案，需先设置其他档案为主档案
        """,
        responses={
            204: OpenApiResponse(description="档案删除成功"),
            400: OpenApiResponse(description="无法删除主档案"),
            403: OpenApiResponse(description="无权限操作"),
            404: OpenApiResponse(description="档案不存在")
        },
        tags=['用户档案']
    )
)
class UserProfileViewSet(viewsets.ModelViewSet):
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        if getattr(self, 'swagger_fake_view', False):
            return UserProfile.objects.none()
        return UserProfile.objects.filter(user=self.request.user, is_active=True)
    
    def get_serializer_class(self):
        if self.action == 'list':
            return UserProfileListSerializer
        elif self.action == 'create':
            return UserProfileCreateSerializer
        return UserProfileSerializer
    
    @extend_schema(
        operation_id='profiles_list',
        summary='获取当前用户的所有档案',
        description='''
        获取当前用户的所有激活档案列表。
        
        **功能特性：**
        - 只返回当前用户的档案
        - 只显示激活状态的档案
        - 返回简化的档案信息
        
        **使用场景：**
        - 用户查看自己的所有档案
        - 选择档案进行操作
        ''',
        responses={
            200: OpenApiResponse(
                description='成功获取档案列表',
                response=UserProfileListSerializer(many=True)
            )
        },
        tags=['Profiles']
    )
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)
    
    @extend_schema(
        operation_id='profiles_create',
        summary='创建新档案',
        description='''
        为当前用户创建新的档案。
        
        **功能特性：**
        - 支持同时创建地址信息
        - 自动关联到当前用户
        - 支持设置主档案
        
        **使用场景：**
        - 用户创建新的个人档案
        - 为不同场景创建专用档案
        ''',
        request=UserProfileCreateSerializer,
        responses={
            201: OpenApiResponse(
                description='档案创建成功',
                response=UserProfileSerializer
            ),
            400: OpenApiResponse(description='请求参数错误')
        },
        tags=['Profiles']
    )
    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        profile = serializer.save()
        
        response_serializer = UserProfileSerializer(profile)
        return Response(response_serializer.data, status=status.HTTP_201_CREATED)
    
    @extend_schema(
        operation_id='profiles_retrieve',
        summary='获取指定档案详情',
        description='''
        获取指定档案的详细信息。
        
        **功能特性：**
        - 返回完整的档案信息
        - 包含地址详细信息
        - 只能访问自己的档案
        
        **使用场景：**
        - 查看档案详情
        - 编辑前获取当前信息
        ''',
        parameters=[
            OpenApiParameter(
                name='id',
                type=OpenApiTypes.INT,
                location=OpenApiParameter.PATH,
                description='档案ID',
                required=True
            )
        ],
        responses={
            200: OpenApiResponse(
                description='成功获取档案详情',
                response=UserProfileSerializer
            ),
            404: OpenApiResponse(description='档案不存在')
        },
        tags=['Profiles']
    )
    def retrieve(self, request, *args, **kwargs):
        return super().retrieve(request, *args, **kwargs)
    
    @extend_schema(
        operation_id='profiles_update',
        summary='更新档案',
        description='''
        更新指定档案的信息。
        
        **功能特性：**
        - 支持部分更新（PATCH）和完整更新（PUT）
        - 只能更新自己的档案
        - 自动更新修改时间
        
        **使用场景：**
        - 修改档案信息
        - 更新个人简介
        - 修改联系方式
        ''',
        parameters=[
            OpenApiParameter(
                name='id',
                type=OpenApiTypes.INT,
                location=OpenApiParameter.PATH,
                description='档案ID',
                required=True
            )
        ],
        request=UserProfileSerializer,
        responses={
            200: OpenApiResponse(
                description='档案更新成功',
                response=UserProfileSerializer
            ),
            400: OpenApiResponse(description='请求参数错误'),
            404: OpenApiResponse(description='档案不存在')
        },
        tags=['Profiles']
    )
    def update(self, request, *args, **kwargs):
        return super().update(request, *args, **kwargs)
    
    @extend_schema(
        operation_id='profiles_partial_update',
        summary='部分更新档案',
        description='''
        部分更新指定档案的信息。
        
        **功能特性：**
        - 只更新提供的字段
        - 只能更新自己的档案
        - 自动更新修改时间
        
        **使用场景：**
        - 快速修改单个字段
        - 更新部分信息
        ''',
        parameters=[
            OpenApiParameter(
                name='id',
                type=OpenApiTypes.INT,
                location=OpenApiParameter.PATH,
                description='档案ID',
                required=True
            )
        ],
        request=UserProfileSerializer,
        responses={
            200: OpenApiResponse(
                description='档案更新成功',
                response=UserProfileSerializer
            ),
            400: OpenApiResponse(description='请求参数错误'),
            404: OpenApiResponse(description='档案不存在')
        },
        tags=['Profiles']
    )
    def partial_update(self, request, *args, **kwargs):
        return super().partial_update(request, *args, **kwargs)
    
    @extend_schema(
        operation_id='profiles_destroy',
        summary='删除档案',
        description='''
        删除指定的档案（软删除）。
        
        **功能特性：**
        - 软删除（设置is_active=False）
        - 只能删除自己的档案
        - 不能删除主档案（如果是唯一档案）
        
        **使用场景：**
        - 删除不需要的档案
        - 清理过期档案
        ''',
        parameters=[
            OpenApiParameter(
                name='id',
                type=OpenApiTypes.INT,
                location=OpenApiParameter.PATH,
                description='档案ID',
                required=True
            )
        ],
        responses={
            204: OpenApiResponse(description='档案删除成功'),
            400: OpenApiResponse(description='不能删除主档案'),
            404: OpenApiResponse(description='档案不存在')
        },
        tags=['Profiles']
    )
    def destroy(self, request, *args, **kwargs):
        profile = self.get_object()
        
        if profile.is_primary and self.get_queryset().count() == 1:
            return Response(
                {'error': '不能删除唯一的主档案'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        profile.is_active = False
        profile.save()
        
        if profile.is_primary:
            remaining_profiles = self.get_queryset().exclude(id=profile.id)
            if remaining_profiles.exists():
                remaining_profiles.first().update(is_primary=True)
        
        return Response(status=status.HTTP_204_NO_CONTENT)
    
    @extend_schema(
        summary="设置主档案",
        description="""将指定档案设置为主档案。
        
        **功能说明：**
        - 将当前档案设为主档案
        - 自动取消其他档案的主档案状态
        - 每个用户只能有一个主档案
        
        **权限要求：** 仅档案所有者可操作
        """,
        request=None,
        responses={
            200: OpenApiResponse(
                response=UserProfileSerializer,
                description="主档案设置成功"
            ),
            403: OpenApiResponse(description="无权限操作"),
            404: OpenApiResponse(description="档案不存在")
        },
        tags=['用户档案']
    )
    @action(detail=True, methods=['post'], url_path='set-primary')
    def set_primary(self, request, pk=None):
        profile = self.get_object()
        
        self.get_queryset().update(is_primary=False)
        
        profile.is_primary = True
        profile.save()
        
        serializer = self.get_serializer(profile)
        return Response(serializer.data)
