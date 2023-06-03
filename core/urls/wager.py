from django.urls import path
from core.views.wager import (
    P2PSportsGameAPIView, SportsWagerAPIView, SportsWagerChallengeAPIView,
    SportAPIView, TeamAPIView, CompetitionAPIView, MarketAPIView
)

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
    path('list', wagers, name='wagers'),
    path('challenges', SportsWagerChallengeAPIView.as_view(), name='wager-challenge'),
    path('games', P2PSportsGameAPIView.as_view(), name='games'),
    path('match', match_wager, name='match-wager'),
    path('game/<pk>/list', game_wagers, name='game-wagers'),
]
