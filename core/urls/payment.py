from django.urls import path
from core.views.user import UserAPIView, UserAccountOwnerAPIView
from core.views.payment import (
    PaymentTransactionAPIView, PaystackPaymentAPIView, FlutterwavePaymentAPIView
)

account_owner = UserAccountOwnerAPIView.as_view({
    'get': 'get_account_owner',
    'put': 'update_user'
})

get_user = UserAPIView.as_view({
    'get': 'get_user',
})

list_banks = FlutterwavePaymentAPIView.as_view({
    'get': 'list_banks'
})

resolve_bank_account = FlutterwavePaymentAPIView.as_view({
    'get': 'resolve_bank_account'
})

charge_card = FlutterwavePaymentAPIView.as_view({
    'get': 'charge_card'
})

validate_charge = FlutterwavePaymentAPIView.as_view({
    'get': 'validate_charge'
})

verify_charge = FlutterwavePaymentAPIView.as_view({
    'get': 'verify_charge'
})

initialize_payout = FlutterwavePaymentAPIView.as_view({
    'get': 'initialize_payout'
})

urlpatterns = [
    path('transactions', PaymentTransactionAPIView.as_view(), name='transactions'),
    path('paystack/bank/list', PaystackPaymentAPIView.as_view({"get": "list_banks"}), name='list-bank'),
    path('paystack/bank/resolve', PaystackPaymentAPIView.as_view({"post": "resolve_bank_details"}), name='resolve-bank-details'),
    path('paystack/deposit/initialize', PaystackPaymentAPIView.as_view({"post": "initialize_deposit"}), name='initialize-deposit'),
    path('paystack/withdraw/initialize', PaystackPaymentAPIView.as_view({"post": "initialize_withdrawal"}), name='initialize-withdrawal'),
    path("flutterwave/banks/<country>", list_banks, name='list-banks'),
	path("flutterwave/bank/resolve", resolve_bank_account, name='resolve_bank_account'),
	path("flutterwave/charge/card", charge_card, name='charge_card'),
	path("flutterwave/validate/charge", validate_charge, name='validate_charge'),
	path("flutterwave/verify/charge", verify_charge, name='verify_charge'),
	path("flutterwave/payout/initialize", initialize_payout, name='initialize_payout'),
]
