from rest_framework import viewsets, status, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, IsAuthenticatedOrReadOnly
from django_filters.rest_framework import DjangoFilterBackend
from drf_spectacular.utils import extend_schema, extend_schema_view, OpenApiParameter, OpenApiResponse
from drf_spectacular.types import OpenApiTypes
from django.db.models import Q
from datetime import datetime

from .models import Event
from .serializers import (
    EventSerializer, 
    EventListSerializer, 
    EventCreateSerializer,
    BuddyRequestSimpleSerializer
)
from matchmaking.models import BuddyRequest
from .filters import EventFilter


@extend_schema_view(
    list=extend_schema(
        summary="获取活动列表",
        description="""获取活动列表，支持多种过滤条件、搜索和排序功能。
        
        **过滤参数：**
        - city: 按城市过滤
        - is_online: 是否线上活动
        - date_from/date_to: 日期范围过滤
        - creator: 按创建者ID过滤
        
        **搜索字段：** title, description, location
        **排序字段：** created_at, start_time, participant_count
        """,
        parameters=[
            OpenApiParameter(
                name='city',
                type=OpenApiTypes.STR,
                location=OpenApiParameter.QUERY,
                description='按城市过滤活动'
            ),
            OpenApiParameter(
                name='date',
                type=OpenApiTypes.DATE,
                location=OpenApiParameter.QUERY,
                description='按日期过滤（YYYY-MM-DD格式）'
            ),
            OpenApiParameter(
                name='search',
                type=OpenApiTypes.STR,
                location=OpenApiParameter.QUERY,
                description='搜索活动名称或介绍'
            ),
            OpenApiParameter(
                name='is_online',
                type=OpenApiTypes.BOOL,
                location=OpenApiParameter.QUERY,
                description='是否为线上活动（true=线上，false=线下）'
            ),
            OpenApiParameter(
                name='date_from',
                type=OpenApiTypes.DATE,
                location=OpenApiParameter.QUERY,
                description='活动开始日期过滤（格式：YYYY-MM-DD）'
            ),
            OpenApiParameter(
                name='date_to',
                type=OpenApiTypes.DATE,
                location=OpenApiParameter.QUERY,
                description='活动结束日期过滤（格式：YYYY-MM-DD）'
            ),
            OpenApiParameter(
                name='creator',
                type=OpenApiTypes.INT,
                location=OpenApiParameter.QUERY,
                description='按创建者用户ID过滤'
            ),
            OpenApiParameter(
                name='ordering',
                type=OpenApiTypes.STR,
                location=OpenApiParameter.QUERY,
                description='排序字段（可选：created_at, start_time, participant_count，前加-表示倒序）'
            )
        ],
        responses={
            200: OpenApiResponse(
                response=EventListSerializer(many=True),
                description="成功返回活动列表"
            )
        },
        tags=['活动管理']
    ),
    create=extend_schema(
        summary="创建活动",
        description="""创建新的活动。
        
        **权限要求：** 需要登录
        **自动设置：** 创建者为当前登录用户
        """,
        request=EventCreateSerializer,
        responses={
            201: OpenApiResponse(
                response=EventSerializer,
                description="活动创建成功"
            ),
            400: OpenApiResponse(description="请求参数错误"),
            401: OpenApiResponse(description="未登录")
        },
        tags=['活动管理']
    ),
    retrieve=extend_schema(
        summary="获取活动详情",
        description="根据活动ID获取详细信息，包括参与者列表和搭子请求统计。",
        responses={
            200: OpenApiResponse(
                response=EventSerializer,
                description="成功返回活动详情"
            ),
            404: OpenApiResponse(description="活动不存在")
        },
        tags=['活动管理']
    ),
    update=extend_schema(
        summary="更新活动",
        description="""完整更新活动信息。
        
        **权限要求：** 仅活动创建者可操作
        """,
        request=EventCreateSerializer,
        responses={
            200: OpenApiResponse(
                response=EventSerializer,
                description="活动更新成功"
            ),
            400: OpenApiResponse(description="请求参数错误"),
            403: OpenApiResponse(description="无权限操作"),
            404: OpenApiResponse(description="活动不存在")
        },
        tags=['活动管理']
    ),
    partial_update=extend_schema(
        summary="部分更新活动",
        description="""部分更新活动信息。
        
        **权限要求：** 仅活动创建者可操作
        """,
        request=EventCreateSerializer,
        responses={
            200: OpenApiResponse(
                response=EventSerializer,
                description="活动更新成功"
            ),
            400: OpenApiResponse(description="请求参数错误"),
            403: OpenApiResponse(description="无权限操作"),
            404: OpenApiResponse(description="活动不存在")
        },
        tags=['活动管理']
    ),
    destroy=extend_schema(
        summary="删除活动",
        description="""删除活动。
        
        **权限要求：** 仅活动创建者可操作
        **注意：** 删除活动会同时删除相关的搭子请求
        """,
        responses={
            204: OpenApiResponse(description="活动删除成功"),
            403: OpenApiResponse(description="无权限操作"),
            404: OpenApiResponse(description="活动不存在")
        },
        tags=['活动管理']
    )
)
class EventViewSet(viewsets.ModelViewSet):
    queryset = Event.objects.select_related('creator', 'location').prefetch_related('buddy_requests')
    permission_classes = [IsAuthenticatedOrReadOnly]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_class = EventFilter
    search_fields = ['name', 'introduction']
    ordering_fields = ['start_time', 'created_at', 'name']
    ordering = ['-created_at']
    
    def get_serializer_class(self):
        if self.action == 'list':
            return EventListSerializer
        elif self.action in ['create', 'update', 'partial_update']:
            return EventCreateSerializer
        return EventSerializer
    
    def get_permissions(self):
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            permission_classes = [IsAuthenticated]
        else:
            permission_classes = [IsAuthenticatedOrReadOnly]
        return [permission() for permission in permission_classes]
    
    def perform_create(self, serializer):
        serializer.save(creator=self.request.user)
    
    def get_object(self):
        obj = super().get_object()
        if self.action in ['update', 'partial_update', 'destroy']:
            if obj.creator != self.request.user:
                self.permission_denied(
                    self.request,
                    message="只有活动创建者可以修改或删除活动"
                )
        return obj
    
    @extend_schema(
        summary="获取活动的搭子请求",
        description="""获取指定活动下当前用户创建的搭子请求列表。
        
        **功能说明：**
        - 仅返回当前用户在该活动下创建的搭子请求
        - 包含请求者信息、状态、参与人数等
        - 按创建时间倒序排列
        
        **权限要求：** 需要登录
        """,
        responses={
            200: OpenApiResponse(
                response=BuddyRequestSimpleSerializer(many=True),
                description="成功返回搭子请求列表"
            ),
            404: OpenApiResponse(description="活动不存在")
        },
        tags=['活动管理']
    )
    @action(detail=True, methods=['get'], url_path='buddy-requests')
    def buddy_requests(self, request, pk=None):
        event = self.get_object()
        # 只返回当前用户在该活动下创建的搭子请求
        buddy_requests = BuddyRequest.objects.filter(
            event=event,
            user=request.user
        ).select_related('user').order_by('-created_at')
        
        serializer = BuddyRequestSimpleSerializer(buddy_requests, many=True)
        return Response(serializer.data)
