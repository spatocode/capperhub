from django_filters import FilterSet, DateTimeFilter
from core.models.tips import Tips
from core.models.user import UserAccount
from core.models.subscription import Subscription


class TipsFilterSet(FilterSet):
    date = DateTimeFilter(field_name='date')
    date__gt = DateTimeFilter(field_name='date', lookup_expr='gt')
    date__lt = DateTimeFilter(field_name='date', lookup_expr='lt')

    class Meta:
        model = Tips
        fields = ['issuer', 'date', 'success', 'published']


class UserAccountFilterSet(FilterSet):

    class Meta:
        model = UserAccount
        fields = ['is_tipster', 'country']


class SubscriptionFilterSet(FilterSet):

    class Meta:
        model = Subscription
        fields = ['issuer', 'subscriber', 'type', 'is_active']
