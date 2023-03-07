from django.urls import path
from core.views import WebhookAPIView

urlpatterns = [
    path('paystack', WebhookAPIView.as_view({"post": "paystack_webhook"}), name='paystack-webhook'),
]
