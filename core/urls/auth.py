from django.urls import path
from dj_rest_auth.registration.views import VerifyEmailView, ConfirmEmailView
from dj_rest_auth.views import (
    LoginView, LogoutView, PasswordResetConfirmView,
    PasswordResetView, PasswordChangeView
)
from core.views.auth import UserAccountRegisterView

urlpatterns = [
    path('register', UserAccountRegisterView.as_view(), name='account_signup'),
    path('login', LoginView.as_view(), name='account_login'),
    path('logout', LogoutView.as_view()),

    path('verify-email/', VerifyEmailView.as_view(), name='rest_verify_email'),
    path('account-confirm-email/', VerifyEmailView.as_view(),
        name='account_email_verification_sent'),
    path('account-confirm-email/<str:key>', ConfirmEmailView.as_view()),

    path('password-reset', PasswordResetView.as_view()),
    path('password-reset-confirm/<uidb64>/<token>', PasswordResetConfirmView.as_view(),
        name='password_reset_confirm'),
    path('password/change', PasswordChangeView.as_view(), name='password_change'),
]
