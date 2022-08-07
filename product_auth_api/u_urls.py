from django.urls import path
from rest_framework_simplejwt import views as jwt_views
from . import views

urlpatterns = [
    path('', views.UserListView.as_view({'get': 'list'}), name='user-list'),
    path('<id>', views.UserInfoView.as_view(), name='user-info'),
]
