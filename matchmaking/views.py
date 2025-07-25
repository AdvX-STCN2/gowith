from rest_framework import viewsets, status, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django_filters.rest_framework import DjangoFilterBackend
from drf_spectacular.utils import extend_schema, extend_schema_view, OpenApiParameter, OpenApiResponse
from drf_spectacular.types import OpenApiTypes
from django.shortcuts import get_object_or_404
from django.db.models import Q
from celery.result import AsyncResult
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

from .models import BuddyRequest, BuddyMatch, UserFeedback, BuddyRequestTag
from .serializers import (
    BuddyRequestSerializer,
    BuddyRequestListSerializer,
    BuddyRequestCreateSerializer,
    BuddyMatchSerializer,
    UserFeedbackSerializer,
    MatchStatusSerializer,
    BuddyRequestTagSerializer
)
from .filters import BuddyRequestFilter
# from .tasks import process_buddy_request_matching  # Celery任务，暂时注释


@extend_schema_view(
    list=extend_schema(
        summary="获取搭子请求列表",
        description="""获取搭子请求列表，支持多种过滤条件、搜索和排序功能。
        
        活动过滤参数：活动
        - activity_type: 按活动类型过滤
        - status: 按状态过滤（open, matched, expired, cancelled）
        - event: 按活动ID过滤
        - has_space: 是否有空位
        - tags: 按标签过滤
        
        活动搜索字段：活动 description, activity_type
        活动排序字段：活动 created_at
        """,
        parameters=[
            OpenApiParameter(
                name='activity_type',
                type=OpenApiTypes.STR,
                location=OpenApiParameter.QUERY,
                description='按活动类型过滤'
            ),
            OpenApiParameter(
                name='status',
                type=OpenApiTypes.STR,
                location=OpenApiParameter.QUERY,
                description='按状态过滤',
                enum=['open', 'matched', 'expired', 'cancelled']
            ),
            OpenApiParameter(
                name='event',
                type=OpenApiTypes.INT,
                location=OpenApiParameter.QUERY,
                description='按活动ID过滤'
            ),
            OpenApiParameter(
                name='has_space',
                type=OpenApiTypes.BOOL,
                location=OpenApiParameter.QUERY,
                description='是否有空位（true=有空位，false=已满员）'
            ),
            OpenApiParameter(
                name='tags',
                type=OpenApiTypes.STR,
                location=OpenApiParameter.QUERY,
                description='按标签过滤（多个标签用逗号分隔）'
            ),
            OpenApiParameter(
                name='search',
                type=OpenApiTypes.STR,
                location=OpenApiParameter.QUERY,
                description='搜索关键词（在描述和活动类型中搜索）'
            ),
            OpenApiParameter(
                name='ordering',
                type=OpenApiTypes.STR,
                location=OpenApiParameter.QUERY,
                description='排序字段（可选：created_at，前加-表示倒序）'
            )
        ],
        responses={
            200: OpenApiResponse(
                response=BuddyRequestListSerializer(many=True),
                description="成功返回搭子请求列表"
            )
        },
        tags=['搭子匹配']
    ),
    create=extend_schema(
        summary="创建搭子请求",
        description="""创建新的搭子请求，系统将自动启动匹配流程。
        
        活动权限要求：活动 需要登录
        活动自动设置：活动 用户为当前登录用户
        活动异步处理：活动 创建成功后会启动后台匹配任务
        """,
        request=BuddyRequestCreateSerializer,
        responses={
            202: OpenApiResponse(
                response={
                    'type': 'object',
                    'properties': {
                        'request_id': {'type': 'integer'},
                        'status_url': {'type': 'string'}
                    }
                },
                description="搭子请求创建成功，匹配任务已启动"
            ),
            400: OpenApiResponse(description="请求参数错误"),
            401: OpenApiResponse(description="未登录")
        },
        tags=['搭子匹配']
    ),
    retrieve=extend_schema(
        summary="获取搭子请求详情",
        description="根据ID获取搭子请求详细信息，包括匹配状态和参与者信息。",
        responses={
            200: OpenApiResponse(
                response=BuddyRequestSerializer,
                description="成功返回搭子请求详情"
            ),
            404: OpenApiResponse(description="搭子请求不存在")
        },
        tags=['搭子匹配']
    ),
    update=extend_schema(
        summary="更新搭子请求",
        description="""完整更新搭子请求信息。
        
        活动权限要求：活动 仅请求创建者可操作
        活动注意：活动 更新后会重新启动匹配流程
        """,
        request=BuddyRequestCreateSerializer,
        responses={
            200: OpenApiResponse(
                response=BuddyRequestSerializer,
                description="搭子请求更新成功"
            ),
            400: OpenApiResponse(description="请求参数错误"),
            403: OpenApiResponse(description="无权限操作"),
            404: OpenApiResponse(description="搭子请求不存在")
        },
        tags=['搭子匹配']
    ),
    partial_update=extend_schema(
        summary="部分更新搭子请求",
        description="""部分更新搭子请求信息。
        
        活动权限要求：活动 仅请求创建者可操作
        活动注意：活动 更新后会重新启动匹配流程
        """,
        request=BuddyRequestCreateSerializer,
        responses={
            200: OpenApiResponse(
                response=BuddyRequestSerializer,
                description="搭子请求更新成功"
            ),
            400: OpenApiResponse(description="请求参数错误"),
            403: OpenApiResponse(description="无权限操作"),
            404: OpenApiResponse(description="搭子请求不存在")
        },
        tags=['搭子匹配']
    ),
    destroy=extend_schema(
        summary="删除搭子请求",
        description="""删除搭子请求。
        
        活动权限要求：活动 仅请求创建者可操作
        活动注意：活动 删除请求会同时删除相关的匹配记录
        """,
        responses={
            204: OpenApiResponse(description="搭子请求删除成功"),
            403: OpenApiResponse(description="无权限操作"),
            404: OpenApiResponse(description="搭子请求不存在")
        },
        tags=['搭子匹配']
    )
)
class BuddyRequestViewSet(viewsets.ModelViewSet):
    """搭子请求视图集"""
    queryset = BuddyRequest.objects.select_related(
        'user', 'profile', 'event'
    ).prefetch_related('tags')
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_class = BuddyRequestFilter
    search_fields = ['description']
    ordering_fields = ['created_at']
    ordering = ['-created_at']
    
    def get_serializer_class(self):
        if self.action == 'list':
            return BuddyRequestListSerializer
        elif self.action in ['create', 'update', 'partial_update']:
            return BuddyRequestCreateSerializer
        return BuddyRequestSerializer
    
    def get_queryset(self):
        if self.action == 'list':
            return self.queryset.filter(status='open')
        return self.queryset
    
    def perform_create(self, serializer):
        buddy_request = serializer.save()
        
        from .tasks import process_buddy_request_matching
        try:
            task_result = process_buddy_request_matching.delay(buddy_request.id)
            buddy_request.celery_task_id = task_result.id
            buddy_request.save(update_fields=['celery_task_id'])
            logger.info(f"为搭子请求 {buddy_request.id} 启动智能匹配任务: {task_result.id}")
        except Exception as e:
            logger.error(f"启动匹配任务失败: {e}")
        
        return buddy_request
    
    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        buddy_request = self.perform_create(serializer)
        
        return Response({
            'request_id': buddy_request.id,
            'status_url': f'/api/requests/{buddy_request.id}/status/'
        }, status=status.HTTP_202_ACCEPTED)
    
    def get_object(self):
        obj = super().get_object()
        if self.action in ['update', 'partial_update', 'destroy']:
            if obj.user != self.request.user:
                self.permission_denied(
                    self.request,
                    message="只有搭子请求创建者可以修改或删除"
                )
        return obj
    
    @extend_schema(
        summary="查询匹配处理状态",
        description="""查询搭子请求的匹配处理状态和进度。
        
        活动功能说明：活动
        - 返回匹配任务的当前状态
        - 包含匹配进度和结果信息
        - 支持实时状态查询
        
        活动状态说明：活动
        - pending: 等待处理
        - processing: 匹配中
        - done: 匹配完成
        - failed: 匹配失败
        """,
        responses={
            200: OpenApiResponse(
                response=MatchStatusSerializer,
                description="成功返回匹配状态"
            ),
            404: OpenApiResponse(description="搭子请求不存在")
        },
        tags=['搭子匹配']
    )
    @action(detail=True, methods=['get'], url_path='status')
    def status(self, request, pk=None):
        buddy_request = self.get_object()
        
        response_data = {
            'request_id': buddy_request.id,
            'status': 'processing',
            'progress': 75,
            'message': '正在进行智能匹配...',
            'created_at': buddy_request.created_at,
            'updated_at': buddy_request.updated_at
        }
        
        if hasattr(buddy_request, 'celery_task_id') and buddy_request.celery_task_id:
            task_result = AsyncResult(buddy_request.celery_task_id)
            
            if task_result.state == 'PENDING':
                response_data['status'] = 'processing'
                response_data['progress'] = 0
                response_data['message'] = '任务正在等待处理...'
            elif task_result.state == 'PROGRESS':
                response_data['status'] = 'processing'
                info = task_result.info or {}
                response_data['progress'] = info.get('progress', 0)
                response_data['message'] = info.get('message', '正在处理匹配请求...')
            elif task_result.state == 'SUCCESS':
                response_data['status'] = 'done'
                response_data['progress'] = 100
                response_data['message'] = '匹配完成！'
            elif task_result.state == 'FAILURE':
                response_data['status'] = 'failed'
                response_data['progress'] = 0
                error_info = str(task_result.info) if task_result.info else '未知错误'
                response_data['message'] = f'匹配失败: {error_info}'
            else:
                response_data['status'] = 'unknown'
                response_data['progress'] = 0
                response_data['message'] = f'未知状态: {task_result.state}'
        else:
            response_data['status'] = 'not_started'
            response_data['progress'] = 0
            response_data['message'] = '匹配尚未开始'
        
        if response_data['status'] == 'done':
            matches = BuddyMatch.objects.filter(buddy_request=buddy_request)
            response_data['matches'] = BuddyMatchSerializer(matches, many=True).data
        
        serializer = MatchStatusSerializer(response_data)
        return Response(serializer.data)
    
    @extend_schema(
        summary="获取最终匹配结果",
        description="""获取搭子请求的最终匹配结果。
        
        活动功能说明：活动
        - 返回该搭子请求的所有匹配记录
        - 包含匹配用户信息和匹配分数
        - 按匹配分数降序排列
        
        活动权限要求：活动 需要登录
        活动返回数据：活动 匹配用户列表，包含用户信息、匹配分数、匹配状态等
        """,
        responses={
            200: OpenApiResponse(
                response=BuddyMatchSerializer(many=True),
                description="成功返回匹配结果列表"
            ),
            404: OpenApiResponse(description="搭子请求不存在")
        },
        tags=['搭子匹配']
    )
    @action(detail=True, methods=['get'], url_path='matches')
    def matches(self, request, pk=None):
        buddy_request = self.get_object()
        matches = BuddyMatch.objects.filter(
            buddy_request=buddy_request
        ).select_related('requester', 'matched_user')
        
        serializer = BuddyMatchSerializer(matches, many=True)
        return Response(serializer.data)


@extend_schema_view(
    list=extend_schema(
        summary="获取匹配结果列表",
        description="获取当前用户相关的匹配结果",
        responses={
            200: BuddyMatchSerializer(many=True)
        }
    ),
    retrieve=extend_schema(
        summary="获取匹配详情",
        description="获取指定匹配的详细信息",
        parameters=[
            OpenApiParameter(
                name='id',
                type=OpenApiTypes.INT,
                location=OpenApiParameter.PATH,
                description='匹配ID'
            )
        ],
        responses={
            200: OpenApiResponse(
                response=BuddyMatchSerializer,
                description="成功返回匹配详情"
            ),
            404: OpenApiResponse(description="匹配不存在")
        }
    )
)
class BuddyMatchViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = BuddyMatchSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['status', 'request']
    ordering_fields = ['matched_at']
    ordering = ['-matched_at']
    
    def get_queryset(self):
        if getattr(self, 'swagger_fake_view', False):
            return BuddyMatch.objects.none()
        return BuddyMatch.objects.filter(
            Q(request__user=self.request.user) | Q(matched_user=self.request.user)
        ).select_related('matched_user', 'request')


@extend_schema_view(
    list=extend_schema(
        summary="获取用户反馈列表",
        description="获取当前用户的反馈记录",
        responses={
            200: UserFeedbackSerializer(many=True)
        }
    ),
    create=extend_schema(
        summary="创建用户反馈",
        description="对匹配的用户进行评价反馈",
        request=UserFeedbackSerializer,
        responses={
            201: OpenApiResponse(
                response=UserFeedbackSerializer,
                description="反馈创建成功"
            ),
            400: OpenApiResponse(description="请求参数错误")
        }
    ),
    retrieve=extend_schema(
        summary="获取反馈详情",
        description="获取指定反馈的详细信息",
        parameters=[
            OpenApiParameter(
                name='id',
                type=OpenApiTypes.INT,
                location=OpenApiParameter.PATH,
                description='反馈ID'
            )
        ],
        responses={
            200: OpenApiResponse(
                response=UserFeedbackSerializer,
                description="成功返回反馈详情"
            ),
            404: OpenApiResponse(description="反馈不存在")
        }
    )
)
class UserFeedbackViewSet(viewsets.ModelViewSet):
    serializer_class = UserFeedbackSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['rating']
    ordering_fields = ['created_at', 'rating']
    ordering = ['-created_at']
    http_method_names = ['get', 'post', 'head', 'options']
    
    def get_queryset(self):
        if getattr(self, 'swagger_fake_view', False):
            return UserFeedback.objects.none()
        return UserFeedback.objects.filter(
            Q(from_user=self.request.user) | Q(to_user=self.request.user)
        ).select_related('from_user', 'to_user')


@extend_schema_view(
    list=extend_schema(
        summary="获取搭子请求标签列表",
        description="获取所有可用的搭子请求标签",
        responses={
            200: BuddyRequestTagSerializer(many=True)
        }
    )
)
class BuddyRequestTagViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = BuddyRequestTag.objects.all()
    serializer_class = BuddyRequestTagSerializer
    permission_classes = [IsAuthenticated]
    ordering = ['name']
