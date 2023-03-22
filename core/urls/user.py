from django.urls import path
from core.views.user import UserAPIView, UserAccountOwnerAPIView, UserWalletAPIView, UserPricingAPIView

account_owner = UserAccountOwnerAPIView.as_view({
    'get': 'get_account_owner'
})

get_user = UserAPIView.as_view({
    'get': 'get_user',
    'put': 'update_user',
})

urlpatterns = [
    path('account', account_owner, name='account-owner'),
    path('pricing', UserPricingAPIView.as_view(), name='user-pricing'),
    path('<username>', get_user, name='users-action'),
    path('wallet/bank/list', UserWalletAPIView.as_view({"get": "list_banks"}), name='list-bank'),
    path('wallet/bank/resolve', UserWalletAPIView.as_view({"post": "resolve_bank_details"}), name='resolve-bank-details'),
    path('wallet/deposit/initialize', UserWalletAPIView.as_view({"post": "initialize_deposit"}), name='initialize-deposit'),
    path('wallet/withdraw/initialize', UserWalletAPIView.as_view({"post": "initialize_withdrawal"}), name='initialize-withdrawal'),
]
