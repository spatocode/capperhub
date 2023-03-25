from django.urls import path
from core.views.webhook import PaystackWebhookAPIView, WhatsappWebhookAPIView

urlpatterns = [
    path('paystack', PaystackWebhookAPIView.as_view(), name='paystack-webhook'),
    path('whatsapp', WhatsappWebhookAPIView.as_view(), name='whatsapp-webhook'),
]
