from django.urls import include, re_path
from django.urls import path
from rest_framework_simplejwt.views import  TokenObtainPairView, TokenRefreshView, TokenVerifyView
from dj_rest_auth.registration.views import VerifyEmailView
from core.views import UserAccountRegisterView

urlpatterns = [
    path('token/obtain', TokenObtainPairView.as_view(), name='login'),
    path('token/refresh', TokenRefreshView.as_view(), name='refresh-token'),
    path('token/verify', TokenVerifyView.as_view(), name='verify-token'),
    path('register', UserAccountRegisterView.as_view(), name='register-user'),
    re_path(r'^account-confirm-email/', VerifyEmailView.as_view(), name='account_email_verification_sent'),
    re_path(r'^account-confirm-email/(?P<key>[-:\w]+)/$', VerifyEmailView.as_view(), name='account_confirm_email'),

    # path('dj-rest-auth/', include('dj_rest_auth.urls')),
    # path('dj-rest-auth/registration/', include('dj_rest_auth.registration.urls'))
    # path('email/verify', VerifyEmailView.as_view(), name='verify-email'),
    # path('token/revoke'),
    # path('password/reset'),
    # path('password/change'),
    # path('email/send/verification'),
    # path('email/resend/verification'),
    # path('health', views.HealthCheckView.as_view(), name='health-check'),
]
