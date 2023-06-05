from django.urls import path
from core.views.webhook import PaystackWebhookAPIView, WhatsappWebhookAPIView, FlutterwaveWebhookAPIView

urlpatterns = [
    path('paystack', PaystackWebhookAPIView.as_view(), name='paystack-webhook'),
    path('flutterwave', FlutterwaveWebhookAPIView.as_view(), name='flutterwave-webhook'),
    path('whatsapp', WhatsappWebhookAPIView.as_view(), name='whatsapp-webhook'),
]
