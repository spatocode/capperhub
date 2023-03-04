from django.urls import path
from core.views import (
    UserAPIView, UserSubscriptionModelViewSet, P2PSportsEventAPIView, PlayAPIView,
    SportsWagerAPIView, UserTransactionAPIView, SportsWagerChallengeAPIView,
    PuntersAPIView
)

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

plays = PlayAPIView.as_view({
    'get': 'get_plays',
    'post': 'create_plays'
})

wagers = SportsWagerAPIView.as_view({
    'post': 'place_wagers',
    'get': 'get_wagers'
})

event_wagers = SportsWagerAPIView.as_view({
    'get': 'get_event_wagers'
})

match_wager = SportsWagerAPIView.as_view({
    'post': 'match_wager'
})

urlpatterns = [
    path('punters', PuntersAPIView.as_view(), name='punters'),
    path('subscriptions', subscriptions, name='user-subscriptions'),
    path('subscribers', subscribers, name='user-subscribers'),
    path('transactions', UserTransactionAPIView.as_view(), name='transactions'),
    path('subscribe', subscribe_user, name='subscribe-user'),
    path('unsubscribe', unsubscribe_user, name='unsubscribe-user'),
    path('plays', plays, name='plays'),
    path('wagers', wagers, name='wagers'),
    path('wager/chalenges', SportsWagerChallengeAPIView.as_view(), name='wager-challenge'),
    path('wager/events', P2PSportsEventAPIView.as_view(), name='events'),
    path('wager/match', match_wager, name='match-wager'),
    path('event/<pk>/wagers', event_wagers, name='event-wagers'),
]
