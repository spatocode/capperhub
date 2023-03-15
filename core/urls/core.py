from django.urls import path
from core.views.core import (
    UserSubscriptionModelViewSet, P2PSportsGameAPIView, PlayAPIView,
    SportsWagerAPIView, UserTransactionAPIView, SportsWagerChallengeAPIView,
    PuntersAPIView, SportAPIView, TeamAPIView, CompetitionAPIView, MarketAPIView
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

plays = PlayAPIView.as_view({
    'get': 'get_plays',
    'post': 'create_plays'
})

wagers = SportsWagerAPIView.as_view({
    'post': 'place_wager',
    'get': 'get_wagers'
})

game_wagers = SportsWagerAPIView.as_view({
    'get': 'get_game_wagers'
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
    path('wager/challenges', SportsWagerChallengeAPIView.as_view(), name='wager-challenge'),
    path('wager/games', P2PSportsGameAPIView.as_view(), name='games'),
    path('wager/match', match_wager, name='match-wager'),
    path('game/<pk>/wagers', game_wagers, name='game-wagers'),
    path('sports', SportAPIView.as_view({"get": "list"}), name='sport-list'),
    path('competitions', CompetitionAPIView.as_view({"get": "list"}), name='competition-list'),
    path('teams', TeamAPIView.as_view({"get": "list"}), name='teams-list'),
    path('markets', MarketAPIView.as_view({"get": "list"}), name='market-list'),
]
