from django.urls import path
from . import views

urlpatterns = [
    path('', views.login, name='login'),
    path('login/', views.login, name='login'),
    path('register/', views.register, name='register'),
    # 加上验证码的路由
    path('get_verify_code/', views.get_verify_code, name='get_verify_code'),
]
from django.urls import path
from . import views

urlpatterns = [
    path('', views.login, name='login'),
    path('login/', views.login, name='login'),
    path('register/', views.register, name='register'),
    path('get_verify_code/', views.get_verify_code, name='get_verify_code'),

    # 新增的主页和结果页路由
    path('index/', views.index, name='index'),
    path('detection/', views.detection, name='detection'),
]