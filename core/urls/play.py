from django.urls import path
from core.views.play import SubscriptionView, PlayAPIView, CappersAPIView

subscriptions = SubscriptionView.as_view({
    'get': 'subscriptions'
})

subscribers = SubscriptionView.as_view({
    'get': 'subscribers'
})

subscribe_user = SubscriptionView.as_view({
    'post': 'subscribe'
})

unsubscribe_user = SubscriptionView.as_view({
    'post': 'unsubscribe'
})

plays = PlayAPIView.as_view({
    'get': 'get_plays',
    'post': 'create_plays'
})

urlpatterns = [
    path('cappers', CappersAPIView.as_view(), name='cappers'),
    path('subscriptions', subscriptions, name='subscriptions'),
    path('subscribers', subscribers, name='subscribers'),
    path('subscribe', subscribe_user, name='subscribe'),
    path('unsubscribe', unsubscribe_user, name='unsubscribe'),
    path('list', plays, name='plays'),
]
