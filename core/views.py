import pytz
from datetime import datetime, timedelta
from django.conf import settings
from django.db.models import Count, Q
from rest_framework.decorators import permission_classes
from rest_framework import authentication, permissions
from rest_framework.views import APIView
from rest_framework.viewsets import ModelViewSet
from rest_framework.response import Response
from dj_rest_auth.registration.views import RegisterView
from rest_framework_simplejwt.views import TokenObtainPairView
from core.permissions import IsOwnerOrReadOnly
from core.serializers import (
    PlaySerializer, UserAccountSerializer, UserAccountRegisterSerializer,
    SubscriptionSerializer, UserPricingSerializer, OwnerUserAccountSerializer,
    OwnerUserSerializer, CustomTokenObtainPairSerializer, UserWalletSerializer,
    P2PSportsBetSerializer, P2PSportsBetInvitationSerializer, TransactionSerializer,
    SportsEventSerializer
)
from core.models.user import UserAccount, Wallet, Pricing
from core.models.transaction import Transaction
from core.models.play import Play
from core.models.bet import P2PSportsBet, P2PSportsBetInvitation, SportsEvent
from core.models.subscription import Subscription
from core.filters import PlayFilterSet, UserAccountFilterSet, SubscriptionFilterSet, P2PSportsBetFilterSet, SportsEventFilterSet
from core.exceptions import SubscriptionError, PricingError, InsuficientFundError, NotFoundError


class CsrfExemptSessionAuthentication(authentication.SessionAuthentication):
    def enforce_csrf(self, request):
        return


class EmailTokenObtainPairView(TokenObtainPairView):
    serializer_class = CustomTokenObtainPairSerializer


class UserAccountRegisterView(RegisterView):
    serializer_class = UserAccountRegisterSerializer

    def perform_create(self, serializer):
        user = super().perform_create(serializer)
        user_account = UserAccount(user=user)
        display_name = serializer.data.get('display_name')
        wallet = Wallet.objects.create()
        pricing = Pricing.objects.create()
        user_account.display_name = display_name
        user_account.wallet = wallet
        user_account.pricing = pricing
        user_account.save()
        return user


@permission_classes((permissions.IsAuthenticated,))
class UserSubscriptionModelViewSet(ModelViewSet):
    serializer_class = SubscriptionSerializer
    filter_class = SubscriptionFilterSet

    def get_object(self, pk):
        try:
            return UserAccount.objects.select_related('pricing', 'currency').get(pk=pk, user__is_active=True)
        except UserAccount.DoesNotExist:
            raise NotFoundError(detail="User not found")

    def subscriptions(self, request):
        useraccount = self.request.user.useraccount
        subscriptions = Subscription.objects.filter(subscriber=useraccount.id, is_active=True).order_by("-subscription_date")
        subscriptions_serializer = self.serializer_class(subscriptions, many=True)

        return Response(subscriptions_serializer.data)

    def subscribers(self, request):
        useraccount = self.request.user.useraccount
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

        if subscription.type == Subscription.PREMIUM and subscription_type == Subscription.PREMIUM:
            if subscription.expiration_date > datetime.utcnow().replace(tzinfo=pytz.UTC):
                raise SubscriptionError(
                    detail='You\'ve already subscribed to Premium plan',
                )

        if subscription.type == Subscription.PREMIUM and subscription_type == Subscription.FREE:
            if subscription.expiration_date > datetime.utcnow().replace(tzinfo=pytz.UTC):
                raise SubscriptionError(
                    detail='You\'ve already subscribed to Premium plan',
                )
        
        return subscription

    def record_transaction(self, subscriber, **kwargs):
        status = kwargs.get('status')
        amount = kwargs.get('amount')
        balance = subscriber.wallet.balance + amount if status == 1 else subscriber.wallet.balance
        transaction = Transaction.objects.create(
            type=Transaction.DEPOSIT,
            user=subscriber,
            payment_issuer=kwargs.get('payment_issuer'),
            channel_type=kwargs.get('channel_type'),
            channel=kwargs.get('channel'),
            amount=amount,
            currency=kwargs.get('currency'),
            status=status,
            balance=balance 
        )

        return transaction

    def subscribe(self, request):
        subscription_type = request.data.get('type')
        tipster_id = request.data.get('tipster')
        period = request.data.get('period')
        amount = request.data.get('amount')
        issuer = request.data.get('issuer')
        subscriber = request.user.useraccount
        tipster = self.get_object(tipster_id)

        previous_subscription = self.verify_subscription(
            subscriber,
            tipster,
            subscription_type=subscription_type
        )

        if subscription_type == Subscription.PREMIUM:
            self.record_transaction(subscriber, amount=amount, issuer=issuer, 
            currency=tipster.currency)

        subscription = Subscription(
            type=subscription_type,
            issuer=tipster,
            subscriber=subscriber,
        )

        if period:
            subscription.period = period
            subscription.expiration_date = datetime.utcnow().replace(tzinfo=pytz.UTC) + timedelta(days=period)

        if previous_subscription and previous_subscription.type == Subscription.FREE and subscription_type == Subscription.PREMIUM:
            previous_subscription.is_active = False
            previous_subscription.save()

        subscription.save()
        serializer = self.serializer_class(instance=subscription)
        return Response({
            "message": "Subscribed successfully",
            "data": serializer.data
        })

    def unsubscribe(self, request, pk=None):
        subscription_type = request.data.get('type')
        tipster_id = request.data.get('tipster')
        subscriber = request.user.useraccount
        tipster = self.get_object(tipster_id)

        try:
            subscription = Subscription.objects.filter(
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


@permission_classes((permissions.IsAuthenticated, IsOwnerOrReadOnly))
class UserPricingAPIView(APIView):

    def get_object(self, pk):
        try:
            return UserAccount.objects.select_related('user', 'pricing').get(pk=pk, user__is_active=True)
        except UserAccount.DoesNotExist:
            raise NotFoundError(detail="User not found")

    def post(self, request, pk=None):
        self.check_object_permissions(request, pk)
        user_account = self.get_object(pk)
        # Make sure pricing can be updated once in 60days
        if user_account.pricing and int(request.data.get("amount")) != user_account.pricing.amount:
            date_due_for_update = user_account.pricing.last_update + timedelta(days=60)
            if date_due_for_update > datetime.utcnow().replace(tzinfo=pytz.UTC):
                raise PricingError(
                    detail='Pricing can only be updated once in 60 days',
                    code=400
                )
        if not user_account.wallet:
            serializer = UserPricingSerializer(data=request.data)
        else:
            serializer = UserPricingSerializer(instance=user_account.pricing, data=request.data)
        serializer.is_valid(raise_exception=True)
        user_pricing = serializer.save()
        user_account.pricing = user_pricing
        user_account.save()
        return Response({
            'message': 'User Pricing Added Successfully',
            'data': serializer.data
        })


@permission_classes((permissions.IsAuthenticated, IsOwnerOrReadOnly))
class UserWalletAPIView(APIView):

    def get_object(self, pk):
        try:
            return UserAccount.objects.select_related('wallet').get(pk=pk, user__is_active=True)
        except UserAccount.DoesNotExist:
            raise NotFoundError(detail="User not found")

    def post(self, request, pk=None):
        self.check_object_permissions(request, pk)
        user_account = self.get_object(pk)
        first_name = request.data.get("first_name")
        last_name = request.data.get("last_name")

        if not user_account.wallet:
            serializer = UserWalletSerializer(data=request.data)
        else:
            serializer = UserWalletSerializer(instance=user_account.wallet, data=request.data)
        serializer.is_valid(raise_exception=True)
        user_wallet = serializer.save()
        user_account.wallet = user_wallet
        if  first_name and last_name:
            user_account.user.first_name = first_name
            user_account.user.last_name = last_name
        user_account.user.save()
        user_account.save()
        return Response({
            'message': 'User Bank Details Added Successfully',
            'data': serializer.data
        })


@permission_classes((permissions.AllowAny, IsOwnerOrReadOnly))
class UserAPIView(ModelViewSet):
    filter_class = UserAccountFilterSet

    def get_object(self, username):
        try:
            return UserAccount.objects.select_related('user').get(user__username=username, user__is_active=True)
        except UserAccount.DoesNotExist:
            raise NotFoundError(detail="User not found")

    def get_account_owner(self, request):
        user_account = UserAccount.objects.get(
            user=request.user.id,
            user__is_active=True
        )
        self.check_object_permissions(request, user_account.id)
        serializer = OwnerUserAccountSerializer(user_account)

        return Response(serializer.data)

    def get_user(self, request, username=None):
        data = self.get_object(username)
        serializer = UserAccountSerializer(data)
        return Response(serializer.data)

    def get_users(self, request, username=None):
        user_ids = [user.id for user in UserAccount.objects.filter(
                user__is_active=True
            ) if user.is_tipster]
        filterset = self.filter_class(
            data=request.query_params,
            queryset=UserAccount.objects.filter(id__in=user_ids).exclude(
                user__first_name=None,
                user__last_name=None,
                wallet=None,
                phone_number=None,
                ip_address=None
            )
        )
        serializer = UserAccountSerializer(filterset.qs, many=True)

        return Response(serializer.data)

    def update_user(self, request, username=None):
        user_account = self.get_object(username)
        self.check_object_permissions(request, user_account.id)
        data = request.data.copy()
        user_serializer = OwnerUserSerializer(
            instance=user_account.user,
            data=data,
            partial=True
        )
        user_serializer.is_valid(raise_exception=True)
        user_serializer.save()

        serializer = OwnerUserAccountSerializer(
            instance=user_account,
            data=data,
            partial=True
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response({
            'message': 'User updated Successfully',
            'data': serializer.data
        })


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

        free_sub_issuers = free_subscriptions.values_list("issuer__id", flat=True)
        pre_sub_issuers = premium_subscriptions.values_list("issuer__id", flat=True)
        filters = Q(issuer=request.user.useraccount.id) | Q(issuer__in=free_sub_issuers, is_premium=False) | Q(issuer__in=pre_sub_issuers, is_premium=True)
        plays = Play.objects.filter(filters).order_by("-date_added")

        query_params = request.query_params
        filterset = self.filter_class(
            data=query_params,
            queryset= plays
        )
        play_serializer = PlaySerializer(filterset.qs, many=True)

        return Response(play_serializer.data)

    def create_plays(self, request):
        #TODO: Confirm the match is valid from probably an API before saving to the DB
        data = request.data
        self.check_object_permissions(request, data.get('issuer'))

        play_serializer = PlaySerializer(data=data)
        play_serializer.is_valid(raise_exception=True)
        play_serializer.save()
        return Response({
            'message': 'Play Created Successfully',
            'data': play_serializer.data
        })


@permission_classes((permissions.IsAuthenticated, IsOwnerOrReadOnly))
class P2PSportsBetAPIView(ModelViewSet):
    p2psportsbet_filter_class = P2PSportsBetFilterSet
    sportsevent_filter_class = SportsEventFilterSet

    def get_bets(self, request):
        filters = Q(backer=request.user.useraccount.id) | Q(layer=request.user.useraccount.id)
        filterset = self.p2psportsbet_filter_class(
            data=request.query_params,
            queryset=P2PSportsBet.objects.filter(filters).order_by("-placed_time")
        )
        p2psportsbet_serializer = P2PSportsBetSerializer(filterset.qs, many=True)

        return Response(p2psportsbet_serializer.data)

    def get_events(self, request):
        filterset = self.sportsevent_filter_class(
            data=request.query_params,
            queryset=SportsEvent.objects.filter()
            .annotate(wager_count=Count("p2psportsbet"))
        )
        sportsevent_serializer = SportsEventSerializer(filterset.qs, many=True)

        return Response(sportsevent_serializer.data)

    def place_bet(self, request):
        data = request.data
        self.check_object_permissions(request, data.get('backer'))
        if request.user.useraccount.wallet.balance < int(data.get("stake")):
            raise InsuficientFundError(detail="You don't have sufficient fund to stake")
        p2psportsbet_serializer = P2PSportsBetSerializer(data=data, partial=True)
        p2psportsbet_serializer.is_valid(raise_exception=True)
        p2psportsbet = p2psportsbet_serializer.save()
        useraccount_wallet = request.user.useraccount.wallet
        useraccount_wallet.withheld = useraccount_wallet.withheld + int(data.get("stake"))
        useraccount_wallet.save()
        if data.get("opponent"):
            self.handle_bet_invitation(p2psportsbet, requestee=data.get("opponent"), requestor=request.user.useraccount)
        return Response({
            'message': 'Bet Challenge Created Successfully',
            'data': p2psportsbet_serializer.data
        })

    def match_bet(self, request, pk):
        p2psportsbet = P2PSportsBet.objects.get(pk=pk)
        if request.user.useraccount.wallet.balance < p2psportsbet.stake:
            raise InsuficientFundError(detail="You don't have sufficient fund to stake")

        p2psportsbet.layer = request.user.useraccount.id
        p2psportsbet.layer_option = request.data.get("layer_option")
        p2psportsbet.matched = True
        p2psportsbet.matched_time = datetime.utcnow().replace(tzinfo=pytz.UTC)
        p2psportsbet.save()

        layer_wallet = request.user.useraccount.wallet
        layer_wallet = layer_wallet.balance - p2psportsbet.stake
        layer_wallet.save()

        backer_wallet = p2psportsbet.backer.wallet
        backer_wallet.balance = backer_wallet.balance - p2psportsbet.stake
        backer_wallet.withheld = backer_wallet.withheld - p2psportsbet.stake
        backer_wallet.save()

        Transaction.objects.bulk_create([
            Transaction(
                type=Transaction.BET,
                amount=p2psportsbet.stake,
                balance=p2psportsbet.backer.wallet.balance - p2psportsbet.stake,
                user=p2psportsbet.backer,
                status=Transaction.SUCCEED,
            ),
            Transaction(
                type=Transaction.BET,
                amount=p2psportsbet.stake,
                balance=request.user.useraccount.wallet.balance - p2psportsbet.stake,
                user=request.user.useraccount,
                status=Transaction.SUCCEED,
            )
        ])

    def handle_bet_invitation(self, bet, requestee=None, requestor=None):
        # TODO: send SMS invitation with a generated link to signup, fund account
        # and accept invitation.
        # Send web socket notification after inviting a registered user
        P2PSportsBetInvitation.objects.create(
            bet=bet,
            requestor=requestor,
            requestee=UserAccount.objects.get(user__username=requestee)
        )

    def get_bet_invitation(self, request):
        bet_list = [invitation.bet.id for invitation in P2PSportsBetInvitation.objects.filter(
            requestee=request.user.useraccount.id,
            accepted=False
        ).select_related("bet").order_by("-date_initialized")]
        queryset = P2PSportsBet.objects.filter(id__in=bet_list)
        p2psportsbet_invitation_serializer = P2PSportsBetSerializer(
            queryset, many=True
        )

        return Response(p2psportsbet_invitation_serializer.data)


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
