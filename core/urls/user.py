from django.urls import path
from core.views import UserAPIView, UserSubscriptionModelViewSet, UserWalletAPIView, UserPricingAPIView, PlayAPIView, P2PBetAPIView, UserTransactionAPIView

subscriptions = UserSubscriptionModelViewSet.as_view({
    'get': 'subscriptions'
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

plays = PlayAPIView.as_view({
    'get': 'get_plays',
    'post': 'create_plays'
})

bets = P2PBetAPIView.as_view({
    'post': 'initialize_bet',
    'get': 'get_bets'
})

urlpatterns = [
    path('tipsters', get_users, name='tipsters'),
    path('subscriptions', subscriptions, name='user-subscriptions'),
    path('account', account_owner, name='account-owner'),
    path('subscribe', subscribe_user, name='subscribe-user'),
    path('unsubscribe', unsubscribe_user, name='unsubscribe-user'),
    path('plays', plays, name='plays'),
    path('bets', bets, name='bets'),
    path('bets/<pk>', P2PBetAPIView.as_view({'post': 'bet_invitation'}), name='bets'),
    path('<username>', get_user, name='users-action'),
    path('<pk>/transactions', UserTransactionAPIView.as_view(), name='transactions'),
    path('<pk>/pricing', UserPricingAPIView.as_view(), name='user-pricing'),
    path('<pk>/wallet', UserWalletAPIView.as_view(), name='user-wallet'),
]
