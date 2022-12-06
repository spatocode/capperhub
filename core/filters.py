from django_filters import FilterSet, DateTimeFilter
from core.models.tips import SportsTips
from core.models.user import UserAccount


class SportsTipsFilterSet(FilterSet):
    date = DateTimeFilter(field_name='date')
    date__gt = DateTimeFilter(field_name='date', lookup_expr='gt')
    date__lt = DateTimeFilter(field_name='date', lookup_expr='lt')

    class Meta:
        model = SportsTips
        fields = ['owner', 'date', 'success', 'is_published']


class UserAccountFilterSet(FilterSet):

    class Meta:
        model = UserAccount
        fields = ['is_tipster', 'price', 'currency', 'country']
