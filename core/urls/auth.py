from django.urls import path, re_path
from dj_rest_auth.registration.views import VerifyEmailView
from dj_rest_auth.views import (
    LoginView, LogoutView, PasswordResetConfirmView,
    PasswordResetView
)
from core.views import UserAccountRegisterView, CustomConfirmEmailView

urlpatterns = [
    path('register', UserAccountRegisterView.as_view(), name='account_signup'),
    path('login', LoginView.as_view(), name='account_login'),
    path('logout', LogoutView.as_view()),

    path('verify-email/', VerifyEmailView.as_view(), name='rest_verify_email'),
    path('account-confirm-email/', VerifyEmailView.as_view(),
        name='account_email_verification_sent'),
    path('account-confirm-email/<str:key>', CustomConfirmEmailView.as_view()),

    path('password-reset', PasswordResetView.as_view()),
    path('password-reset-confirm/<uidb64>/<token>', PasswordResetConfirmView.as_view(),
        name='password_reset_confirm'),
]
