from django.urls import path
from core.views import UserAPIView, UserSubscriptionModelViewSet, UserWalletAPIView, UserPricingAPIView, PlayAPIView, P2PSportsBetAPIView, UserTransactionAPIView

subscriptions = UserSubscriptionModelViewSet.as_view({
    'get': 'subscriptions'
})

subscribers = UserSubscriptionModelViewSet.as_view({
    'get': 'subscribers'
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
})

get_users = UserAPIView.as_view({
    'get': 'get_users'
})

plays = PlayAPIView.as_view({
    'get': 'get_plays',
    'post': 'create_plays'
})

bets = P2PSportsBetAPIView.as_view({
    'post': 'place_bet',
    'get': 'get_bets'
})

bet_events = P2PSportsBetAPIView.as_view({
    'get': 'get_events'
})

bet_invitations = P2PSportsBetAPIView.as_view({
    'get': 'get_bet_invitation',
    'post': 'accept_bet_invitation'
})

urlpatterns = [
    path('tipsters', get_users, name='tipsters'),
    path('subscriptions', subscriptions, name='user-subscriptions'),
    path('subscribers', subscribers, name='user-subscribers'),
    path('transactions', UserTransactionAPIView.as_view(), name='transactions'),
    path('account', account_owner, name='account-owner'),
    path('subscribe', subscribe_user, name='subscribe-user'),
    path('unsubscribe', unsubscribe_user, name='unsubscribe-user'),
    path('plays', plays, name='plays'),
    path('bets', bets, name='bets'),
    path('bets/invitations', bet_invitations, name='bets'),
    path('bets/events', bet_events, name='bets'),
    path('bets/match', P2PSportsBetAPIView.as_view({'post': 'match_bet'}), name='bets'),
    path('<username>', get_user, name='users-action'),
    path('<pk>/pricing', UserPricingAPIView.as_view(), name='user-pricing'),
    path('<pk>/wallet', UserWalletAPIView.as_view(), name='user-wallet'),
]
