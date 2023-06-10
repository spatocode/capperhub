import pytz
from datetime import datetime, timedelta
from django.conf import settings
from django.db.models import Count, Q
from django.core.cache import cache
from django.core.cache.backends.base import DEFAULT_TIMEOUT
from rest_framework.decorators import permission_classes
from rest_framework import authentication, permissions
from rest_framework.views import APIView
from rest_framework.viewsets import ModelViewSet
from rest_framework.response import Response
from core.permissions import IsOwnerOrReadOnly
from core.serializers import (
    PlaySerializer, UserAccountSerializer, SubscriptionSerializer,
    SportsWagerSerializer, TransactionSerializer, SportsGameSerializer, TeamSerializer,
    CompetitionSerializer, SportSerializer, MarketSerializer, PlaySlipSerializer
)
from core.models.user import UserAccount
from core.models.transaction import Transaction
from core.models.play import Play, PlaySlip
from core.models.wager import SportsWager, SportsWagerChallenge
from core.models.games import SportsGame, Sport, Competition, Team, Market
from core.models.subscription import Subscription
from core.filters import PlayFilterSet, UserAccountFilterSet, SubscriptionFilterSet, SportsWagerFilterSet, SportsGameFilterSet
from core.exceptions import SubscriptionError, InsuficientFundError, NotFoundError, ForbiddenError, PermissionDeniedError
from core.shared.helper import sync_records, sync_subscriptions, notify_subscribers


class CsrfExemptSessionAuthentication(authentication.SessionAuthentication):
    def enforce_csrf(self, request):
        return


@permission_classes((permissions.IsAuthenticated,))
class UserSubscriptionView(ModelViewSet):
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
            queryset= plays
        )
        play_serializer = PlaySlipSerializer(filterset.qs, many=True)

        return Response(play_serializer.data)

    def create_plays(self, request):
        #TODO: Confirm the match is valid from probably an API before saving to the DB
        data = request.data.copy()
        self.check_object_permissions(request, request.user.useraccount.id)
        sync_subscriptions(issuer=request.user.useraccount.id)
        play_slip = PlaySlip.objects.create(
            issuer=request.user.useraccount,
            is_premium=data.get("is_premium"),
            title=data.get("title"),
        )
        data['slip'] = play_slip
        PlaySerializer(data=data.get("plays"), many=True)
        plays = [Play(slip=play_slip, **play) for play in data.get("plays")]
        Play.objects.bulk_create(plays)
        play_slip_serializer = PlaySlipSerializer(PlaySlip.objects.get(id=play_slip.id))
        data = play_slip_serializer.data
        notify_subscribers(data)
        return Response({
            'message': 'Play Created Successfully',
            'data': data
        })


@permission_classes((permissions.IsAuthenticated, IsOwnerOrReadOnly))
class SportsWagerAPIView(ModelViewSet):
    filter_class = SportsWagerFilterSet

    def get_wagers(self, request):
        filters = Q(backer=request.user.useraccount.id) | Q(layer=request.user.useraccount.id)
        filterset = self.filter_class(
            data=request.query_params,
            queryset=SportsWager.objects.filter(filters).order_by("-placed_time")
        )
        serializer = SportsWagerSerializer(filterset.qs, many=True)

        return Response(serializer.data)

    def get_game_wagers(self, request, pk=None):
        try:
            games = SportsGame.objects.get(pk=pk)
        except SportsGame.DoesNotExist:
            raise NotFoundError(detail="Game not found")
        queryset = games.wagers.all()
        serializer = SportsWagerSerializer(queryset, many=True)

        return Response(serializer.data)

    def place_wager(self, request):
        data = request.data
        self.check_object_permissions(request, data.get('backer'))
        if request.user.useraccount.wallet.balance < int(data.get("stake")):
            raise InsuficientFundError(detail="You don't have sufficient fund to stake")
        serializer = SportsWagerSerializer(data=data, partial=True)
        serializer.is_valid(raise_exception=True)
        sports_wager = serializer.save()
        game_serializer = SportsGameSerializer(sports_wager.game)
        useraccount_wallet = request.user.useraccount.wallet
        useraccount_wallet.withheld = useraccount_wallet.withheld + int(data.get("stake"))
        useraccount_wallet.balance = useraccount_wallet.balance - int(data.get("stake"))
        useraccount_wallet.save()
        if data.get("opponent"):
            self.handle_wager_invitation(sports_wager, requestee=data.get("opponent"), requestor=request.user.useraccount)
        return Response({
            'message': 'Wager Challenge Created Successfully',
            'data': serializer.data
        })

    def match_wager(self, request):
        # TODO: Send websocket notifications
        try:
            sports_wager = SportsWager.objects.select_related("backer", "game", "transaction").get(pk=request.data.get("wager"))
        except SportsWager.DoesNotExist:
            raise NotFoundError(detail="Wager not found")

        if request.user.useraccount.wallet.balance < sports_wager.stake:
            raise InsuficientFundError(detail="You don't have sufficient fund to stake")

        if sports_wager.game.result:
            raise ForbiddenError(detail="Game no longer available for wager")
        
        if sports_wager.matched:
            raise ForbiddenError(detail="Wager no longer available to play")

        if sports_wager.backer.id == request.user.useraccount.id:
            raise PermissionDeniedError(detail="Action not permitted")

        serializer = sync_records(
            sports_wager,
            request.user.useraccount,
            layer_option=request.data.get("layer_option")
        )
        return Response({
            'message': 'Wager matched successfully',
            'data': serializer.data
        })

    def handle_wager_invitation(self, wager, requestee=None, requestor=None):
        # TODO: send SMS invitation with a generated link to signup, fund account
        # and accept invitation.
        # Send web socket notification after inviting a registered user
        user = UserAccount.objects.get(user__username=requestee)
        if requestor.id == user.id:
            raise PermissionDeniedError(detail="Action not permitted")
        SportsWagerChallenge.objects.create(
            wager=wager,
            requestor=requestor,
            requestee=user
        )


@permission_classes((permissions.AllowAny,))
class P2PSportsGameAPIView(APIView):
    filter_class = SportsGameFilterSet

    def get(self, request):
        filterset = self.filter_class(
            data=request.query_params,
            queryset=SportsGame.objects.all()
            .annotate(wager_count=Count("wagers"))
        )
        serializer = SportsGameSerializer(filterset.qs, many=True)

        return Response(serializer.data)


@permission_classes((permissions.IsAuthenticated, IsOwnerOrReadOnly))
class SportsWagerChallengeAPIView(APIView):
    def get(self, request):
        """Get wager challenges"""
        # TODO: Add invitation date_initialized to the returned SportsWager queryset
        # Find better ways to optimize this operation
        wager_list = [challenge.wager.id for challenge in SportsWagerChallenge.objects.filter(
            requestee=request.user.useraccount.id,
            accepted=False
        ).select_related("wager").order_by("-date_initialized")]
        queryset = SportsWager.objects.filter(id__in=wager_list)
        serializer = SportsWagerSerializer(
            queryset, many=True
        )

        return Response(serializer.data)
    
    def post(self, request):
        """Accept wager challenges"""
        # TODO: Send websocket notifications
        try:
            queryset = SportsWager.objects.select_related("backer").get(
                id=request.data.get("wager")
            )
        except SportsWager.DoesNotExist:
            raise NotFoundError(detail="Wager not found")

        if request.user.useraccount.wallet.balance < queryset.stake:
            raise InsuficientFundError(detail="You don't have sufficient fund to stake")

        try:
            invitation = queryset.invitation.get(requestee=request.user.useraccount)
        except queryset.invitation.DoesNotExist:
            raise PermissionDeniedError(detail="Action not permitted")
        
        if queryset.backer.id == request.user.useraccount.id:
            raise PermissionDeniedError(detail="Action not permitted")

        if queryset.matched:
            raise ForbiddenError(detail="Wager no longer available to play")

        invitation.accepted = True
        invitation.save()

        serializer = sync_records(
            queryset,
            request.user.useraccount,
            layer_option=request.data.get("layer_option")
        )

        return Response({
            "message": "Challenge accepted",
            "data": serializer.data
        })


@permission_classes((permissions.IsAuthenticated, IsOwnerOrReadOnly))
class UserTransactionAPIView(APIView):
    def get_object(self, pk):
        try:
            return UserAccount.objects.get(pk=pk, user__is_active=True)
        except UserAccount.DoesNotExist:
            raise NotFoundError(detail="User not found")
    
    def get(self, request):
        self.check_object_permissions(request, request.user.useraccount.id)
        useraccount = request.user.useraccount
        transactions = useraccount.user_transactions.all()
        serializer = TransactionSerializer(instance=transactions, many=True)
        return Response(serializer.data)


@permission_classes((permissions.IsAuthenticated,))
class TeamAPIView(ModelViewSet):
    serializer_class = TeamSerializer

    def get_queryset(self):
        cache_key = 'team'
        if cache_key in cache:
            data = cache.get(cache_key)
        else:
            queryset = Team.objects.filter(
                competition__name=self.request.query_params.get('competition')
            )
            data = queryset
            cache.set(cache_key, data, timeout=settings.CACHE_TTL)
        return data


@permission_classes((permissions.IsAuthenticated,))
class SportAPIView(ModelViewSet):
    serializer_class = SportSerializer

    def get_queryset(self):
        cache_key = 'sport'
        if cache_key in cache:
            data = cache.get(cache_key)
        else:
            queryset = Sport.objects.filter()
            data = queryset
            cache.set(cache_key, data, timeout=settings.CACHE_TTL)
        return data


@permission_classes((permissions.IsAuthenticated,))
class CompetitionAPIView(ModelViewSet):
    serializer_class = CompetitionSerializer

    def get_queryset(self):
        cache_key = 'competition'
        if cache_key in cache:
            data = cache.get(cache_key)
        else:
            queryset = Competition.objects.filter(
                sport__name=self.request.query_params.get('sport')
            )
            data = queryset
            cache.set(cache_key, data, timeout=settings.CACHE_TTL)
        return data


@permission_classes((permissions.IsAuthenticated,))
class MarketAPIView(ModelViewSet):
    serializer_class = MarketSerializer

    def get_queryset(self):
        cache_key = 'market'
        if cache_key in cache:
            data = cache.get(cache_key)
        else:
            queryset = Market.objects.filter(
                sport__name=self.request.query_params.get('sport')
            )
            data = queryset
            cache.set(cache_key, data, timeout=settings.CACHE_TTL)
            return data
