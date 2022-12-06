from django.conf.urls import include
from django.contrib import admin
from django.urls import path

urlpatterns = [
    path('admin/', admin.site.urls),
    path('auth/', include('core.urls.auth')),
    path('users/', include('core.urls.user')),
    path('tips/', include('core.urls.tips')),
]
