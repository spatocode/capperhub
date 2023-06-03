from django.conf import settings
from django.conf.urls.static import static
from django.conf.urls import include
from django.contrib import admin
from django.urls import path

urlpatterns = [
    path('admin/', admin.site.urls),
    path('auth/', include('core.urls.auth')),
    path('user/', include('core.urls.user')),
    path('play/', include('core.urls.play')),
    path('wager/', include('core.urls.wager')),
    path('payment/', include('core.urls.payment')),
    path('misc/', include('core.urls.misc')),
    path('webhook/', include('core.urls.webhook')),
    path('__debug__/', include('debug_toolbar.urls'))
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
