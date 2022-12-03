from django.urls import path
from rest_framework_simplejwt import views as jwt_views
from core.views.auth import UserAPIView

urlpatterns = [
    path('register', UserAPIView.as_view(), name='register-user'),
    # path('token/obtain', views.UserTokenObtainPairView.as_view(), name='login'),
    # path('token/refresh', jwt_views.TokenRefreshView.as_view(), name='refresh-token'),
    # # path('token/revoke'),
    # # path('password/reset'),
    # # path('password/change'),
    # # path('email/send/verification'),
    # # path('email/resend/verification'),
    # # path('email/verify'),
    # path('health', views.HealthCheckView.as_view(), name='health-check'),
]
