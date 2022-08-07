from django.conf.urls import include
from django.contrib import admin
from django.urls import path

urlpatterns = [
    path('admin/', admin.site.urls),
    path('auth/', include('product_auth_api.urls')),
    path('users/', include('product_auth_api.u_urls')),
    path('products/', include('product_api.urls')),
]
