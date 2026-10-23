from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),
    # 把所有非 admin 的请求都交给 app01 去处理
    path('', include('app01.urls')),
]
