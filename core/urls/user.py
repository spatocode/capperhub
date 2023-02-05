from django.urls import path
from core.views import UserAPIView, UserSubscriptionModelViewSet, UserWalletAPIView, UserPricingAPIView, TipsAPIView

subscriptions = UserSubscriptionModelViewSet.as_view({
    'get': 'list'
})

subscribe_user = UserSubscriptionModelViewSet.as_view({
    'post': 'subscribe'
})

unsubscribe_user = UserSubscriptionModelViewSet.as_view({
    'post': 'unsubscribe'
})

account_owner = UserAPIView.as_view({
    'get': 'get_account_owner'
})

get_user = UserAPIView.as_view({
    'get': 'get_user',
    'put': 'update_user',
    'delete': 'delete_user'
})

get_users = UserAPIView.as_view({
    'get': 'get_users'
})

urlpatterns = [
    path('tipsters', get_users, name='users'),
    path('subscriptions', subscriptions, name='user-subscriptions'),
    path('account', account_owner, name='account-owner'),
    path('subscribe', subscribe_user, name='subscribe-user'),
    path('unsubscribe', unsubscribe_user, name='unsubscribe-user'),
    path('<username>', get_user, name='users-action'),
    path('<pk>/tips', TipsAPIView.as_view(), name='tips'),
    path('<pk>/pricing', UserPricingAPIView.as_view(), name='user-pricing'),
    path('<pk>/wallet', UserWalletAPIView.as_view(), name='user-wallet'),
]
