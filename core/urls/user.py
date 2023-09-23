from django.urls import path
from core.views.user import UserAPIView, UserAccountOwnerAPIView, UserUpgradeAPIView

account_owner = UserAccountOwnerAPIView.as_view({
    'get': 'get_account_owner',
    'put': 'update_user'
})

get_user = UserAPIView.as_view({
    'get': 'get_user',
})

urlpatterns = [
    path('account', account_owner, name='account-owner'),
    path('upgrade', UserUpgradeAPIView, name='upgrade'),
    # path('pricing', UserPricingAPIView.as_view(), name='user-pricing'),
    # path('payment', UserPaymentDetailsAPIView.as_view(), name='user-payment'),
    path('<username>', get_user, name='users-action'),
]
