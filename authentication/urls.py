from django.urls import path
from . import views

urlpatterns = [
    path('login/', views.casdoor_login, name='casdoor_login'),
    path('callback/', views.casdoor_callback, name='casdoor_callback'),
    path('logout/', views.casdoor_logout, name='casdoor_logout'),
    path('user/', views.get_user_info, name='get_user_info'),
]