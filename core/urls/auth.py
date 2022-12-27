from django.urls import include, re_path
from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView, TokenVerifyView
from dj_rest_auth.registration.views import VerifyEmailView
from core.views import UserAccountRegisterView, EmailTokenObtainPairView

urlpatterns = [
    path('token/obtain', EmailTokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('token/refresh', TokenRefreshView.as_view(), name='token_refresh'),
    path('token/verify', TokenVerifyView.as_view(), name='token_verify'),
    path('register', UserAccountRegisterView.as_view(), name='user_register'),
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
