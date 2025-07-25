from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import UserProfileViewSet

app_name = 'profiles'

router = DefaultRouter()
router.register(r'profiles', UserProfileViewSet, basename='profile')

urlpatterns = [
    path('api/', include(router.urls)),
]