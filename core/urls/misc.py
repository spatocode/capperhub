from django.urls import path
from core.views.misc import FeedbackAPIView, WaitlistAPIView, TermsOfUseAPIView, PrivacyPolicyAPIView

urlpatterns = [
    path('feedback', FeedbackAPIView.as_view(), name='terms_of_use'),
    path('waitlist', WaitlistAPIView.as_view(), name='privacy_policy'),
    path('docs/terms', TermsOfUseAPIView.as_view(), name='terms_of_use'),
    path('docs/privacy-policy', PrivacyPolicyAPIView.as_view(), name='privacy_policy'),
]
