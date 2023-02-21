from django_filters import FilterSet, DateTimeFilter
from core.models.play import Play
from core.models.bet import P2PBet
from core.models.user import UserAccount
from core.models.subscription import Subscription


class P2PBetFilterSet(FilterSet):
    date_initialized = DateTimeFilter(field_name='date_initialized')
    date_initialized__gt = DateTimeFilter(field_name='date_initialized', lookup_expr='gt')
    date_initialized__lt = DateTimeFilter(field_name='date_initialized', lookup_expr='lt')

    class Meta:
        model = P2PBet
        fields = ['issuer', 'date_initialized', 'status']


class PlayFilterSet(FilterSet):
    match_day = DateTimeFilter(field_name='match_day')
    match_day__gt = DateTimeFilter(field_name='match_day', lookup_expr='gt')
    match_day__lt = DateTimeFilter(field_name='match_day', lookup_expr='lt')

    class Meta:
        model = Play
        fields = ['issuer', 'match_day', 'status']


class UserAccountFilterSet(FilterSet):

    class Meta:
        model = UserAccount
        fields = ['country']


class SubscriptionFilterSet(FilterSet):

    class Meta:
        model = Subscription
        fields = ['issuer', 'subscriber', 'type', 'is_active']
