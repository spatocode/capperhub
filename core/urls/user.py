from django.urls import include, re_path
from django.urls import path
from core.views import UserAPIView, UserSubscriptionModelViewSet

subscribers = UserSubscriptionModelViewSet.as_view({
    'get': 'list'
})

subscribe_user = UserSubscriptionModelViewSet.as_view({
    'post': 'subscribe'
})

unsubscribe_user = UserSubscriptionModelViewSet.as_view({
    'delete': 'unsubscribe'
})

urlpatterns = [
    path('', UserAPIView.as_view(), name='users'),
    path('<pk>', UserAPIView.as_view(), name='users-action'),
    path('<pk>/subscribers', subscribers, name='user-subscribers'),
    path('<pk>/subscribe', subscribe_user, name='subscribe-user'),
    path('<pk>/unsubscribe', unsubscribe_user, name='unsubscribe-user'),
]
