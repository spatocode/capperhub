from django_filters import FilterSet, DateTimeFilter
from core.models.play import Play
from core.models.user import UserAccount
from core.models.subscription import Subscription


class PlayFilterSet(FilterSet):
    date = DateTimeFilter(field_name='date')
    date__gt = DateTimeFilter(field_name='date', lookup_expr='gt')
    date__lt = DateTimeFilter(field_name='date', lookup_expr='lt')

    class Meta:
        model = Play
        fields = ['issuer', 'date', 'status']


class UserAccountFilterSet(FilterSet):

    class Meta:
        model = UserAccount
        fields = ['country']


class SubscriptionFilterSet(FilterSet):

    class Meta:
        model = Subscription
        fields = ['issuer', 'subscriber', 'type', 'is_active']
