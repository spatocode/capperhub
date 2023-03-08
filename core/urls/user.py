from django.urls import path
from core.views import UserAPIView, UserWalletAPIView, UserPricingAPIView

account_owner = UserAPIView.as_view({
    'get': 'get_account_owner'
})

get_user = UserAPIView.as_view({
    'get': 'get_user',
    'put': 'update_user',
})

urlpatterns = [
    path('account', account_owner, name='account-owner'),
    path('<username>', get_user, name='users-action'),
    path('pricing', UserPricingAPIView.as_view(), name='user-pricing'),
    path('wallet/bank', UserWalletAPIView.as_view({"post": "update_bank_details"}), name='wallet-update-bank'),
    path('wallet/bank/list', UserWalletAPIView.as_view({"get": "list_banks"}), name='wallet-update-bank'),
    path('wallet/bank/resolve', UserWalletAPIView.as_view({"post": "resolve_bank_details"}), name='wallet-update-bank'),
    path('wallet/deposit/initialize', UserWalletAPIView.as_view({"post": "initialize_deposit"}), name='initialize-deposit'),
    path('wallet/withdraw/initialize', UserWalletAPIView.as_view({"post": "initialize_withdrawal"}), name='initialize-withdrawal'),
]
