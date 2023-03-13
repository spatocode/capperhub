import json
import hashlib
import pytz
from datetime import datetime, timedelta
from django.conf import settings
from django.db.models import Count, Q
from rest_framework.decorators import permission_classes
from rest_framework import authentication, permissions
from rest_framework.views import APIView
from rest_framework.viewsets import ModelViewSet
from rest_framework.response import Response
from rest_framework import status
from dj_rest_auth.registration.views import RegisterView
from rest_framework_simplejwt.views import TokenObtainPairView
from dj_rest_auth.registration.views import ConfirmEmailView
from paystackapi.transaction import Transaction as PaystackTransaction
from paystackapi.verification import Verification
from paystackapi.misc import Misc
from paystackapi.trecipient import TransferRecipient
from paystackapi.transfer import Transfer
from core.permissions import IsOwnerOrReadOnly
from core.serializers import (
    PlaySerializer, UserAccountSerializer, UserAccountRegisterSerializer,
    SubscriptionSerializer, UserPricingSerializer, OwnerUserAccountSerializer,
    OwnerUserSerializer, CustomTokenObtainPairSerializer, OwnerUserWalletSerializer,
    SportsWagerSerializer, TransactionSerializer, SportsGameSerializer, TeamSerializer,
    CompetitionSerializer, SportSerializer, MarketSerializer, PlaySlipSerializer
)
from core.models.user import UserAccount, Wallet, Pricing
from core.models.transaction import Transaction, Currency
from core.models.play import Play, PlaySlip
from core.models.wager import SportsWager, SportsWagerChallenge
from core.models.games import SportsGame, Sport, Competition, Team, Market
from core.models.subscription import Subscription
from core.filters import PlayFilterSet, UserAccountFilterSet, SubscriptionFilterSet, SportsWagerFilterSet, SportsGameFilterSet
from core.exceptions import SubscriptionError, PricingError, InsuficientFundError, NotFoundError, ForbiddenError, PermissionDeniedError
from core.shared.helper import sync_records, sync_subscriptions
from core.shared.model_utils import generate_reference_code
from core import ws


class CsrfExemptSessionAuthentication(authentication.SessionAuthentication):
    def enforce_csrf(self, request):
        return


class EmailTokenObtainPairView(TokenObtainPairView):
    serializer_class = CustomTokenObtainPairSerializer


class UserAccountRegisterView(RegisterView):
    serializer_class = UserAccountRegisterSerializer

    def perform_create(self, serializer):
        user = super().perform_create(serializer)
        user.is_active = False
        user.save()
        user_account = user.useraccount
        user_account.display_name = serializer.data.get('display_name')
        user_account.country = serializer.data.get('country')
        wallet = Wallet.objects.create(currency=Currency.objects.get(country=user_account.country))
        pricing = Pricing.objects.create()
        user_account.wallet = wallet
        user_account.pricing = pricing
        user_account.save()
        return user


class CustomConfirmEmailView(ConfirmEmailView):
    def post(self, *args, **kwargs):
        redirect = super().post(*args, **kwargs)
        user = self.object.email_address.user
        user.is_active = True
        user.save()
        return redirect


@permission_classes((permissions.IsAuthenticated,))
class UserSubscriptionModelViewSet(ModelViewSet):
    serializer_class = SubscriptionSerializer
    filter_class = SubscriptionFilterSet

    def get_object(self, pk):
        try:
            return UserAccount.objects.select_related('pricing').get(pk=pk, user__is_active=True)
        except UserAccount.DoesNotExist:
            raise NotFoundError(detail="User not found")

    def subscriptions(self, request):
        useraccount = self.request.user.useraccount
        sync_subscriptions(subscriber=useraccount.id)
        subscriptions = Subscription.objects.filter(subscriber=useraccount.id, is_active=True).order_by("-subscription_date")
        subscriptions_serializer = self.serializer_class(subscriptions, many=True)

        return Response(subscriptions_serializer.data)

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
        amount = kwargs.get('amount')
        balance = subscriber.wallet.balance - amount
        transaction = Transaction.objects.create(
            type=Transaction.PURCHASE,
            user=subscriber,
            payment_issuer=kwargs.get('payment_issuer'),
            channel=kwargs.get('channel'),
            amount=amount,
            currency=kwargs.get('currency'),
            status=Transaction.SUCCEED,
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
            if subscriber.wallet.balance < int(amount):
                raise InsuficientFundError(detail="You don't have sufficient funds to subscribe")
            self.record_transaction(subscriber, amount=amount, issuer=issuer, currency=tipster.currency)

        subscription = Subscription.objects.get_or_create(
            type=subscription_type,
            issuer=tipster,
            subscriber=subscriber,
            is_active=True
        )

        if period:
            subscription[0].period = period
            subscription[0].expiration_date = datetime.utcnow().replace(tzinfo=pytz.UTC) + timedelta(days=period)

        if previous_subscription and previous_subscription.type == Subscription.FREE and subscription_type == Subscription.PREMIUM:
            previous_subscription.is_active = False
            previous_subscription.save()

        serializer = self.serializer_class(instance=subscription[0])
        ws.notify_update_user_subscribe(serializer.data)
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


@permission_classes((permissions.IsAuthenticated,))
class UserPricingAPIView(APIView):

    def post(self, request):
        user_account = request.user.useraccount
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


@permission_classes((permissions.AllowAny,))
class WebhookAPIView(ModelViewSet):

    def record_successful_deposit_transaction(request):
        data = request.data.get("data")
        user = UserAccount.objects.get(user__email=data["customer"]["email"])
        wallet = user.wallet
        wallet.balance = wallet.balance + data.get("amount")
        wallet.authorizations = [data.get("authorization")] + wallet.authorizations
        wallet.save()
        Transaction.objects.create(
            type=Transaction.DEPOSIT,
            status=Transaction.SUCCEED,
            amount=data.get("amount"),
            channel=data.get("channel"),
            currency=data.get("currency"),
            time=data.get("paid_at"),
            reference=data.get("reference"),
            payment_issuer=Transaction.PAYSTACK,
            balance=wallet.balance,
            user=user
        )

    def record_successful_withdrawal_transaction(request):
        data = request.data.get("data")
        transaction = Transaction.objects.select_related("user").get(reference=data.get("reference"))
        transaction.status = Transaction.SUCCEED
        transaction.updated_at = data.get("updated_at")
        transaction.save()

    def verify_origin(self, request):
        xps_header = request.headers.get("x-paystack-signature")
        secret = settings.PAYSTACK_SECRET_KEY
        body_bytes = json.dumps(request.data).encode("utf-8")
        hash = hashlib.new("sha512", secret)
        hash.update(body_bytes)
        hash_digest = hash.hexdigest()
        return hash_digest == xps_header

    def paystack_webhook(self, request):
        event = request.data.get("event")
        is_verified_origin = self.verify_origin(request)
        if is_verified_origin:
            #TODO: Handle more events
            if event == "charge.success":
                self.record_successful_deposit_transaction(request)
            elif event == "transfer.success":
                self.record_successful_withdrawal_transaction(request)
        return Response(status=status.HTTP_200_OK)


@permission_classes((permissions.IsAuthenticated,))
class UserWalletAPIView(ModelViewSet):
    #TODO: Handle all errors from payment processor
    def initialize_deposit(self, request):
        if request.data.get("authorization_code"):
            response = PaystackTransaction.charge(
                amount=int(request.data.get("amount")) * 100,
                email=request.user.email,
                authorization_code=request.data.get("authorization_code")
            )
            return Response(response)
        response = PaystackTransaction.initialize(
            amount=int(request.data.get("amount")) * 100,
            email=request.user.email
        )
        return Response(response)

    def initialize_withdrawal(self, request):
        user = request.user.useraccount
        userwallet = user.wallet
        amount = request.data.get("amount")
        if userwallet.balance < int(amount):
            raise InsuficientFundError(detail="You don't have sufficient fund to withdraw")
        type = "nuban" if user.country.name == "Nigeria" else "mobile_money"
        tr_response = TransferRecipient.create(
            type=type,
            name=request.data.get("name"),
            account_number=request.data.get("account_number"),
            bank_code=request.data.get("bank_code"),
            currency=userwallet.currency.code,
        )

        if tr_response.get("status") == True:
            recipient_code = tr_response.get("data")["recipient_code"]
            userwallet.recipent_code = recipient_code
            reference = generate_reference_code()
            userwallet.save()
            response = Transfer.initiate(
                source="balance",
                recipient=recipient_code,
                amount=amount,
                reason="Predishun Gaming Ltd. Withdrawal",
                reference=reference
            )
            if response.get("status") == True:
                userwallet.balance = userwallet.balance - int(amount)
                userwallet.save()
                Transaction.objects.create(
                    type=Transaction.WITHDRAWAL,
                    status=Transaction.PENDING,
                    amount=amount,
                    channel="bank",
                    currency=userwallet.currency,
                    reference=reference,
                    payment_issuer=Transaction.PAYSTACK,
                    balance=userwallet.balance,
                    user=user
                )
                return Response(response)

        return Response(tr_response, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def list_banks(self, request):
        response = Misc.list_banks(country=request.user.useraccount.country.name)
        return Response(response)

    def resolve_bank_details(self, request):
        response = Verification.verify_account(
            account_number=request.data.get("account_number"),
            bank_code=request.data.get("bank_code")
        )
        return Response(response)

    def update_bank_details(self, request):
        user_account = request.user.useraccount
        first_name = request.data.get("first_name")
        last_name = request.data.get("last_name")

        if not user_account.wallet:
            serializer = OwnerUserWalletSerializer(data=request.data)
        else:
            serializer = OwnerUserWalletSerializer(instance=user_account.wallet, data=request.data)
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


@permission_classes((permissions.AllowAny,))
class PuntersAPIView(APIView):
    filter_class = UserAccountFilterSet

    def get(self, request, username=None):
        user_ids = [user.id for user in UserAccount.objects.filter(
                user__is_active=True
            ) if user.is_punter]
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
        ws.notify_update_user_play(play_slip_serializer.data)
        return Response({
            'message': 'Play Created Successfully',
            'data': play_slip_serializer.data
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
        ws.notify_update_game(game_serializer.data)
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
        queryset = Team.objects.filter(
            competition__name=self.request.query_params.get('competition')
        )
        return queryset


@permission_classes((permissions.IsAuthenticated,))
class SportAPIView(ModelViewSet):
    serializer_class = SportSerializer

    def get_queryset(self):
        queryset = Sport.objects.filter()
        return queryset


@permission_classes((permissions.IsAuthenticated,))
class CompetitionAPIView(ModelViewSet):
    serializer_class = CompetitionSerializer

    def get_queryset(self):
        queryset = Competition.objects.filter(
            sport__name=self.request.query_params.get('sport')
        )
        return queryset


@permission_classes((permissions.IsAuthenticated,))
class MarketAPIView(ModelViewSet):
    serializer_class = MarketSerializer

    def get_queryset(self):
        queryset = Market.objects.filter(
            sport__name=self.request.query_params.get('sport')
        )
        return queryset
