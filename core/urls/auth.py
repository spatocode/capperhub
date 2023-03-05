from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView, TokenVerifyView
from dj_rest_auth.registration.views import VerifyEmailView
from dj_rest_auth.views import (
    LoginView, LogoutView, PasswordChangeView, PasswordResetConfirmView,
    PasswordResetView
)
from core.views import UserAccountRegisterView, EmailTokenObtainPairView

urlpatterns = [
    path('token/obtain', EmailTokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('token/refresh', TokenRefreshView.as_view(), name='token_refresh'),
    path('token/verify', TokenVerifyView.as_view(), name='token_verify'),
    path('register', UserAccountRegisterView.as_view(), name='user_register'),
    path('login', LoginView.as_view()),
    path('logout', LogoutView.as_view()),
    path('password/reset', PasswordResetView.as_view(), name='rest_password_reset'),
    path('password/reset/confirm', PasswordResetConfirmView.as_view(), name='rest_password_reset_confirm'),
    path('password/change', PasswordChangeView.as_view(), name='rest_password_change'),
    path('email/verify', VerifyEmailView.as_view(), name='verify-email'),
]
