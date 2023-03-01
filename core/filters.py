from django_filters.rest_framework import FilterSet, DateTimeFilter, BooleanFilter
from core.models.play import Play
from core.models.bet import P2PSportsBet
from core.models.user import UserAccount
from core.models.subscription import Subscription


class P2PSportsBetFilterSet(FilterSet):
    matched = BooleanFilter(field_name="matched")

    class Meta:
        model = P2PSportsBet
        fields = ['matched']


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
