import pytz
from datetime import datetime, timedelta
from django.conf import settings
from django.db.models import Q
from django.core.cache import cache
from rest_framework.decorators import permission_classes
from rest_framework import authentication, permissions
from rest_framework.views import APIView
from rest_framework.viewsets import ModelViewSet
from rest_framework.response import Response
from core.permissions import IsOwnerOrReadOnly
from core.serializers import (
    PlaySerializer, UserAccountSerializer, SubscriptionSerializer, PlaySlipSerializer
)
from core.models.user import UserAccount
from core.models.transaction import Transaction
from core.models.play import Play, PlaySlip, Match
from core.models.subscription import Subscription
from core.filters import PlayFilterSet, UserAccountFilterSet, SubscriptionFilterSet
from core.exceptions import SubscriptionError, InsuficientFundError, NotFoundError
from core.shared.helper import sync_subscriptions, notify_subscribers
from core import ws


class CsrfExemptSessionAuthentication(authentication.SessionAuthentication):
    def enforce_csrf(self, request):
        return


@permission_classes((permissions.IsAuthenticated,))
class SubscriptionView(ModelViewSet):
    serializer_class = SubscriptionSerializer
    filter_class = SubscriptionFilterSet

    def get_object(self, pk):
        try:
            return UserAccount.objects.select_related('pricing', 'wallet').get(pk=pk, user__is_active=True)
        except UserAccount.DoesNotExist:
            raise NotFoundError(detail="User not found")

    def subscriptions(self, request):
        useraccount = self.request.user.useraccount
        sync_subscriptions(subscriber=useraccount.id)
        subscriptions = Subscription.objects.filter(subscriber=useraccount.id, is_active=True).order_by("-subscription_date")
        subscriptions_serializer = self.serializer_class(subscriptions, many=True)
        data = subscriptions_serializer.data
        return Response(data)

    def subscribers(self, request):
        useraccount = self.request.user.useraccount
        sync_subscriptions(issuer=useraccount.id)
        subscribers = Subscription.objects.filter(issuer=useraccount.id, is_active=True).order_by("-subscription_date")
        subscribers_serializer = self.serializer_class(subscribers, many=True)

        return Response(subscribers_serializer.data)

    def verify_subscription(self, subscriber, issuer, **kwargs):
        subscription_type = kwargs.get('subscription_type')

        if subscriber.id == issuer.id:
            raise SubscriptionError(
                detail='Self subscription not permitted',
            )

        try:
            subscription = Subscription.objects.filter(
                subscriber=subscriber,
                issuer=issuer,
                is_active=True
            ).latest('subscription_date')
        except Subscription.DoesNotExist:
            return

        if subscription.type == Subscription.FREE and subscription_type == Subscription.FREE:
            raise SubscriptionError(
                detail='You\'ve already subscribed to Free plan',   
            )

        if subscription.type == Subscription.PREMIUM and subscription_type == Subscription.PREMIUM or (subscription.type == Subscription.PREMIUM and subscription_type == Subscription.FREE):
            if subscription.expiration_date > datetime.utcnow().replace(tzinfo=pytz.UTC):
                raise SubscriptionError(
                    detail='You\'ve already subscribed to Premium plan',
                )
        
        return subscription

    def record_transaction(self, subscriber, **kwargs):
        amount = kwargs.get('amount')
        transaction = Transaction.objects.create(
            type=Transaction.PURCHASE,
            user=subscriber,
            payment_issuer=kwargs.get('payment_issuer'),
            channel=kwargs.get('channel'),
            amount=amount,
            currency=kwargs.get('currency'),
            status=Transaction.SUCCEED,
            balance=kwargs.get("subscriber_balance")
        )

        return transaction

    def sync_wallet_records(self, amount, **kwargs):
        charge_fee = settings.PERCENTAGE_CHARGE * amount
        amount_after_charge = amount - charge_fee

        tipster_wallet = kwargs.get("tipster_wallet")
        tipster_wallet.balance = tipster_wallet.balance + amount_after_charge
        tipster_wallet.save()

        subscriber_wallet = kwargs.get("subscriber_wallet")
        subscriber_wallet.balance = kwargs.get("subscriber_balance")
        subscriber_wallet.save()

    def subscribe(self, request):
        subscription_type = request.data.get('type')
        tipster_id = request.data.get('tipster')
        period = request.data.get('period')
        amount = request.data.get('amount')
        subscriber = request.user.useraccount
        tipster = self.get_object(tipster_id)

        previous_subscription = self.verify_subscription(
            subscriber,
            tipster,
            subscription_type=subscription_type
        )

        if subscription_type == Subscription.PREMIUM:
            if subscriber.wallet.balance < int(amount):
                raise InsuficientFundError(detail="You don't have sufficient funds to subscribe")

        subscription = Subscription.objects.get_or_create(
            type=subscription_type,
            issuer=tipster,
            subscriber=subscriber,
            is_active=True,
        )

        if period:
            subscription[0].period = period
            subscription[0].expiration_date = datetime.utcnow().replace(tzinfo=pytz.UTC) + timedelta(days=period)
            subscription[0].save()

        if previous_subscription and previous_subscription.type == Subscription.FREE and subscription_type == Subscription.PREMIUM:
            previous_subscription.is_active = False
            previous_subscription.save()

        if subscription_type == Subscription.PREMIUM:
            subscriber_balance = subscriber.wallet.balance - amount
            self.sync_wallet_records(amount, tipster_wallet=tipster.wallet, subscriber_wallet=subscriber.wallet, subscriber_balance=subscriber_balance)
            self.record_transaction(subscriber, amount=amount, currency=tipster.wallet.currency, subscriber_balance=subscriber_balance)

        data = self.serializer_class(instance=subscription[0]).data

        ws.notify_update_user_subscribe(data)
        return Response({
            "message": "Subscribed successfully",
            "data": data
        })

    def unsubscribe(self, request, pk=None):
        subscription_type = int(request.data.get('type'))
        tipster_id = request.data.get('tipster')
        subscriber = request.user.useraccount
        tipster = self.get_object(tipster_id)

        try:
            subscription = Subscription.objects.filter(
                type=subscription_type,
                subscriber=subscriber,
                issuer=tipster,
                is_active=True
            ).latest('subscription_date')
        except Subscription.DoesNotExist:
            raise SubscriptionError(
                detail="You're not subscribed to this plan",
                code=400
            )

        if subscription.type != subscription_type:
            raise SubscriptionError(
                detail="You're not subscribed to this plan",
                code=400
            )

        subscription.is_active = False
        subscription.save()
        serializer = self.serializer_class(instance=subscription)
        ws.notify_update_user_unsubscribe(serializer.data)
        return Response({"message": "Unsubscribed successfully", "data": serializer.data})


@permission_classes((permissions.AllowAny,))
class CappersAPIView(APIView):
    filter_class = UserAccountFilterSet

    def get(self, request, username=None):
        cache_key = 'punters'
        if cache_key in cache:
            data = cache.get(cache_key)
        else:
            filterset = self.filter_class(
            data=request.query_params,
            queryset=UserAccount.objects.filter(
                playslip__date_added__gt=datetime.utcnow().replace(tzinfo=pytz.UTC)-timedelta(days=14)
            ).distinct().exclude(
                user__first_name=None,
                user__last_name=None,
                wallet=None,
                phone_number=None,
                ip_address=None
            )
            )
            serializer = UserAccountSerializer(filterset.qs, many=True)
            data = serializer.data
            cache.set(cache_key, data, timeout=settings.CACHE_TTL)

        return Response(data)


@permission_classes((permissions.IsAuthenticated, IsOwnerOrReadOnly))
class PlayAPIView(ModelViewSet):
    filter_class = PlayFilterSet

    def get_plays(self, request):
        free_subscriptions = Subscription.objects.filter(
            subscriber=request.user.useraccount.id,
            type=0,
            is_active=True
        )
        premium_subscriptions = Subscription.objects.filter(
            subscriber=request.user.useraccount.id,
            type=1,
            is_active=True
        )

        free_sub_date = free_subscriptions.values_list("subscription_date", flat=True)
        pre_sub_date = premium_subscriptions.values_list("subscription_date", flat=True)
        filters = Q(issuer=request.user.useraccount.id)

        for date in free_sub_date:
            filters = filters | Q(date_added__gte=date, is_premium=False)

        for date in pre_sub_date:
            filters = filters | Q(date_added__gte=date, is_premium=True)

        plays = PlaySlip.objects.filter(filters).order_by("-date_added")

        query_params = request.query_params
        filterset = self.filter_class(
            data=query_params,
            queryset=plays
        )
        play_serializer = PlaySlipSerializer(filterset.qs, many=True)

        return Response(play_serializer.data)

    def create_plays(self, request):
        #TODO: Confirm the match is valid from probably an API before saving to the DB
        data = request.data.copy()
        self.check_object_permissions(request, request.user.useraccount.id)
        sync_subscriptions(issuer=request.user.useraccount.id)
        #TODO: Redesign this process
        play_slip = PlaySlip.objects.create(
            issuer=request.user.useraccount,
            is_premium=data.get("is_premium"),
            title=data.get("title"),
        )
        data['slip'] = play_slip
        PlaySerializer(data=data.get("plays"), many=True)
        plays = []
        for play in data.get("plays"):
            match = Match.objects.create(**play.pop("match"))
            Play(slip=play_slip, match=match, **play)
        Play.objects.bulk_create(plays)
        play_slip_serializer = PlaySlipSerializer(PlaySlip.objects.get(id=play_slip.id))
        data = play_slip_serializer.data
        notify_subscribers(data)
        return Response({
            'message': 'Play Created Successfully',
            'data': data
        })
