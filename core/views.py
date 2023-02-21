import pytz
from datetime import datetime, timedelta
from django.conf import settings
from django.core import exceptions
from django.db.models import Q
from django.http.response import Http404
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
    P2PBetSerializer, P2PBetInvitationSerializer, TransactionSerializer
)
from core.models.user import UserAccount
from core.models.transaction import Transaction
from core.models.play import Play
from core.models.bet import P2PBet, P2PBetInvitation
from core.models.subscription import Subscription
from core.filters import PlayFilterSet, UserAccountFilterSet, SubscriptionFilterSet, P2PBetFilterSet
from core.exceptions import SubscriptionError, PricingError, InsuficientFundError


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
        is_tipster = serializer.data.get('is_tipster')
        if is_tipster:
            user_account.is_tipster = is_tipster
        user_account.save()
        return user


@permission_classes((permissions.IsAuthenticated,))
class UserSubscriptionModelViewSet(ModelViewSet):
    serializer_class = SubscriptionSerializer
    filter_class = SubscriptionFilterSet

    def get_object(self, pk):
        try:
            return UserAccount.objects.select_related('pricing', 'currency').get(pk=pk)
        except UserAccount.DoesNotExist:
            raise Http404

    def subscriptions(self, request):
        useraccount = self.request.user.useraccount

        subscriptions = Subscription.objects.filter(subscriber=useraccount.id, is_active=True).order_by("-subscription_date")
        subscribers = Subscription.objects.filter(issuer=useraccount.id, is_active=True).order_by("-subscription_date")
        subscriptions_serializer = self.serializer_class(subscriptions, many=True)
        subscribers_serializer = self.serializer_class(subscribers, many=True)

        return Response({
            "subscriptions": subscriptions_serializer.data,
            "subscribers": subscribers_serializer.data
        })

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
            payment_issuer=kwargs.get('ipayment_issuer'),
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
            period=period,
            subscription_type=subscription_type
        )

        if subscription_type == Subscription.PREMIUM:
            self.record_transaction(subscriber, amount=amount, issuer=issuer, 
            currency=tipster.currency, period=period)

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

        self.verify_subscription_permission(subscriber, tipster)
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
            return UserAccount.objects.select_related('user', 'pricing').get(pk=pk)
        except UserAccount.DoesNotExist:
            raise Http404

    def post(self, request, pk=None):
        self.check_object_permissions(request, pk)
        data = request.data
        user_account = self.get_object(pk)
        # Make sure pricing can be updated once in 60days
        if user_account.pricing:
            date_due_for_update = user_account.pricing.date + timedelta(days=60)
            if date_due_for_update > datetime.utcnow().replace(tzinfo=pytz.UTC):
                raise PricingError(
                    detail='Pricing can only be updated once in 60 days',
                    code=400
                )
        serializer = UserPricingSerializer(data=data)
        serializer.is_valid(raise_exception=True)
        user_pricing = serializer.save()
        if not user_account.pricing:
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
            return UserAccount.objects.select_related('wallet').get(pk=pk)
        except UserAccount.DoesNotExist:
            raise Http404

    def post(self, request, pk=None):
        self.check_object_permissions(request, pk)
        user_account = self.get_object(pk)

        serializer = UserWalletSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user_wallet = serializer.save()
        if not user_account.wallet:
            user_account.wallet = user_wallet
        user_account.save()
        return Response({
            'message': 'User Bank Details Added Successfully',
            'data': serializer.data
        })


@permission_classes((permissions.AllowAny, IsOwnerOrReadOnly))
class UserAPIView(ModelViewSet):
    filter_class = UserAccountFilterSet

    def get_object(self, username, request):
        try:
            return UserAccount.objects.select_related('user').get(user__username=username)
        except UserAccount.DoesNotExist:
            raise Http404

    def get_account_owner(self, request):
        user_account = UserAccount.objects.get(
            user=request.user.id
        )
        self.check_object_permissions(request, user_account.id)
        serializer = OwnerUserAccountSerializer(user_account)

        return Response(serializer.data)

    def get_user(self, request, username=None):
        data = self.get_object(username, request)
        serializer = UserAccountSerializer(data)
        return Response(serializer.data)

    def get_users(self, request, username=None):
        query_params = request.query_params
        user_ids = [user.id for user in UserAccount.objects.filter(
                user__is_active=True
            ).exclude(
                user__first_name=None,
                user__last_name=None,
                country=None,
                bio=None,
                display_name=None
            ) if user.is_tipster]
        filterset = self.filter_class(
            data=query_params,
            queryset=UserAccount.objects.filter(id__in=user_ids)
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


@permission_classes((permissions.IsAuthenticated,))
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

        if int(data.get('issuer')) != request.user.useraccount.id:
            raise exceptions.PermissionDenied()

        play_serializer = PlaySerializer(data=data)
        play_serializer.is_valid(raise_exception=True)
        play_serializer.save()
        return Response({
            'message': 'Play Created Successfully',
            'data': play_serializer.data
        })


@permission_classes((permissions.IsAuthenticated,))
class P2PBetAPIView(ModelViewSet):
    filter_class = P2PBetFilterSet

    def get_bets(self, request):
        filterset = self.filter_class(
            data=request.query_params,
            queryset=P2PBet.objects.all().order_by("-placed_time")
        )
        p2pbet_serializer = P2PBetSerializer(filterset.qs, many=True)

        return Response(p2pbet_serializer.data)

    def place_bet(self, request):
        data = request.data
        if request.user.useraccount.wallet.balance < data.get("stake_per_bettor"):
            raise InsuficientFundError(detail="You don't have sufficient fund to stake")
        p2pbet_serializer = P2PBetSerializer(data=data, partial=True)
        p2pbet_serializer.is_valid(raise_exception=True)
        p2pbet_serializer.save()
        useraccount_wallet = request.user.useraccount.wallet
        useraccount_wallet.withheld = useraccount_wallet.withheld + int(data.get("stake_per_bettor"))
        return Response({
            'message': 'Bet Challenge Created Successfully',
            'data': p2pbet_serializer.data
        })

    def match_bet(self, request, pk):
        p2pbet = P2PBet.objects.get(pk=pk)
        if request.user.useraccount.wallet.balance < p2pbet.stake_per_bettor:
            raise InsuficientFundError(detail="You don't have sufficient fund to stake")

        p2pbet.layer = request.user.useraccount.id
        p2pbet.layer_option = request.data.get("layer_option")
        p2pbet.matched = True
        p2pbet.matched_time = datetime.utcnow().replace(tzinfo=pytz.UTC)
        p2pbet.save()

        layer_wallet = request.user.useraccount.wallet
        layer_wallet = layer_wallet.balance - p2pbet.stake_per_bettor
        layer_wallet.save()

        backer_wallet = p2pbet.backer.wallet
        backer_wallet.balance = backer_wallet.balance - p2pbet.stake_per_bettor
        backer_wallet.withheld = backer_wallet.withheld - p2pbet.stake_per_bettor
        backer_wallet.save()

        Transaction.objects.bulk_create([
            Transaction(
                type=Transaction.BET,
                amount=p2pbet.stake_per_bettor,
                balance=p2pbet.backer.wallet.balance - p2pbet.stake_per_bettor,
                user=p2pbet.backer,
                status=Transaction.SUCCEED,
            ),
            Transaction(
                type=Transaction.BET,
                amount=p2pbet.stake_per_bettor,
                balance=request.user.useraccount.wallet.balance - p2pbet.stake_per_bettor,
                user=request.user.useraccount,
                status=Transaction.SUCCEED,
            )
        ])

    def bet_invitation(self, request, pk=None):
        try:
            requestee = UserAccount.objects.get(phone_number=request.data.get("requestee"))
        except UserAccount.DoesNotExist:
            # TODO: send SMS invitation with a generated link to signup, fund account
            # and accept invitation
            pass
        p2pbet = P2PBet.objects.get(id=pk)
        p2pbet_invitation = P2PBetInvitation.objects.create(
            bet=p2pbet,
            requestor=request.user.useraccount,
            requestee=requestee
        )
        p2pbet_invitation_serializer = P2PBetInvitationSerializer(p2pbet_invitation)
        return Response({
            "message": "Bet Invitation Sent Successfully",
            "data": p2pbet_invitation_serializer.data
        })

@permission_classes((permissions.IsAuthenticated, IsOwnerOrReadOnly))
class UserTransactionAPIView(APIView):

    def get_object(self, pk):
        try:
            return UserAccount.objects.get(pk=pk)
        except UserAccount.DoesNotExist:
            raise Http404
    
    def get(self, request, pk=None):
        self.check_object_permissions(self.request, pk)
        useraccount = self.get_object(pk)
        transactions = useraccount.user_transactions.all()
        serializer = TransactionSerializer(instance=transactions, many=True)
        return Response(serializer.data)
