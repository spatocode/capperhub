import pytz
from datetime import datetime
from django.db.models import Count
from django_filters.rest_framework import FilterSet, DateTimeFilter, BooleanFilter
from core.models.play import Play
from core.models.wager import SportsWager
from core.models.games import SportsGame
from core.models.user import UserAccount
from core.models.subscription import Subscription


class SportsWagerFilterSet(FilterSet):
    matched = BooleanFilter(field_name="matched")
    expired = BooleanFilter(method="expired_filter")

    def expired_filter(self, queryset, name, value):
        if value:
            return queryset.filter(
                game__match_day__lt=datetime.utcnow().replace(tzinfo=pytz.UTC)
            )
        return queryset

    class Meta:
        model = SportsWager
        fields = ['matched', 'expired']


class SportsGameFilterSet(FilterSet):
    top = BooleanFilter(method="top_filter")
    open = BooleanFilter(method="open_filter")
    latest = BooleanFilter(method="latest_filter")
    expired = BooleanFilter(method="expired_filter")

    def top_filter(self, queryset, name, value):
        if value:
            return queryset.order_by('-wager_count')
        return queryset

    def open_filter(self, queryset, name, value):
        if value:
            return queryset.filter(match_day__gt=datetime.utcnow().replace(tzinfo=pytz.UTC))
        return queryset

    def expired_filter(self, queryset, name, value):
        if value:
            return queryset.filter(
                match_day__lt=datetime.utcnow().replace(tzinfo=pytz.UTC)
            )
        return queryset

    def latest_filter(self, queryset, name, value):
        if value:
            return queryset.order_by('-time_added')
        return queryset

    class Meta:
        model = SportsGame
        fields = ["top", "open", "latest"]


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
