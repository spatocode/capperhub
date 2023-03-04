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
    path('<pk>/pricing', UserPricingAPIView.as_view(), name='user-pricing'),
    path('<pk>/wallet', UserWalletAPIView.as_view(), name='user-wallet'),
]
