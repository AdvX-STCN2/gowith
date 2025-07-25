from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    BuddyRequestViewSet,
    BuddyMatchViewSet,
    UserFeedbackViewSet,
    BuddyRequestTagViewSet
)

router = DefaultRouter()
router.register(r'requests', BuddyRequestViewSet, basename='buddy-request')
router.register(r'matches', BuddyMatchViewSet, basename='buddy-match')
router.register(r'feedback', UserFeedbackViewSet, basename='user-feedback')
router.register(r'tags', BuddyRequestTagViewSet, basename='buddy-request-tag')

urlpatterns = [
    path('api/', include(router.urls)),
]