from django.urls import path
from product_api import views


product = views.ProductView.as_view({
    'post': 'create',
    'get': 'list',
})

product_subscription = views.ProductSubscriptionView.as_view({
    'post': 'subscribe',
    'delete': 'unsubscribe',
})

product_picks = views.ProductPicksView.as_view({
    # 'post': 'create',
    'get': 'list',
    # 'delete': 'delete',
})

urlpatterns = [
    path('', product, name='product'),
    path('<product_id>', views.ProductInfoView.as_view(), name='product-info'),
    path('subscribe/<product_id>', product_subscription, name='product-subscription'),
    path('<product_id>/subscribers', views.ProductSubscribersView.as_view(), name='product-subscribers'),
    path('<product_id>/picks', product_picks, name='product-picks'),
]
