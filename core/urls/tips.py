from django.urls import include, re_path
from django.urls import path
from core.views import SportsTipsAPIView

urlpatterns = [
    path('', SportsTipsAPIView.as_view(), name='tips'),
    path('<pk>', SportsTipsAPIView.as_view(), name='tips-action'),
]
