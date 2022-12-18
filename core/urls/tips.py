from django.urls import include, re_path
from django.urls import path
from core.views import TipsAPIView

urlpatterns = [
    path('create', TipsAPIView.as_view(), name='tips'),
    path('<pk>', TipsAPIView.as_view(), name='tips-action'),
]
