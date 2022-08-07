from django_filters import FilterSet, NumberFilter, CharFilter
from product_api.models.base import Product


class ProductFilter(FilterSet):
    type = NumberFilter()
    price = NumberFilter()
    owner = CharFilter(field_name='owner__user__username')
    currency = CharFilter(field_name='currency__code')

    class Meta:
        model = Product
        fields = ['owner', 'currency']
