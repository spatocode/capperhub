from django.conf.urls import include
from django.contrib import admin
from django.urls import path

urlpatterns = [
    path('admin/', admin.site.urls),
    path('auth/', include('core.urls.auth')),
    path('user/', include('core.urls.user')),
    path('core/', include('core.urls.core')),
    path('webhook/', include('core.urls.webhook')),
    path('__debug__/', include('debug_toolbar.urls'))
]
