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

product_subscribers = views.ProductSubscribersView.as_view({
    'get': 'list'
})

product_picks = views.ProductPicksView.as_view({
    'post': 'create',
    'get': 'list',
    'delete': 'delete',
})

urlpatterns = [
    path('', product, name='product'),
    path('<product_id>', views.ProductInfoView.as_view(), name='product-info'),
    path('subscribe/<product_id>', product_subscription, name='product-subscription'),
    path('subscribers', product_subscribers, name='product-subscribers'),
    path('picks', product_picks, name='product-picks'),
]
