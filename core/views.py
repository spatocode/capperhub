import pytz
from datetime import datetime, timedelta
from django.conf import settings
from django.core import exceptions
from django.http.response import Http404
from rest_framework.decorators import permission_classes
from rest_framework import authentication, permissions
from rest_framework.views import APIView
from rest_framework.viewsets import ModelViewSet
from rest_framework.response import Response
from dj_rest_auth.registration.views import RegisterView
from paystackapi.subaccount import SubAccount
from rest_framework_simplejwt.views import TokenObtainPairView
from core.permissions import BettorPermissionOrReadOnly, TipsterPermission, IsOwnerOrReadOnly, IsOwnerOrSubscriberReadOnly
from core.serializers import (
    MatchTipsSerializer, UserAccountSerializer, UserAccountRegisterSerializer,
    SubscriptionSerializer, UserPricingSerializer, OwnerUserAccountSerializer,
    OwnerUserSerializer, CustomTokenObtainPairSerializer, UserWalletSerializer,
    BookingCodeTipsSerializer
)
from core.models.user import UserAccount
from core.models.currency import Currency
from core.models.tips import MatchTips, BookingCodeTips
from core.models.subscription import Subscription, Payment
from core.filters import TipsFilterSet, UserAccountFilterSet, SubscriptionFilterSet
from core.exceptions import SubscriptionError, PricingError, PaymentSetupError, PermissionDeniedError, BadRequestError


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


@permission_classes((permissions.IsAuthenticated, BettorPermissionOrReadOnly))
class UserSubscriptionModelViewSet(ModelViewSet):
    serializer_class = SubscriptionSerializer
    filter_class = SubscriptionFilterSet

    def get_object(self, pk):
        try:
            return UserAccount.objects.select_related('pricing', 'currency').get(pk=pk)
        except UserAccount.DoesNotExist:
            raise Http404

    def get_queryset(self):
        query_params = self.request.query_params
        issuer = query_params.dict().get("issuer")
        subscriber = query_params.dict().get("subscriber")
        useraccount = self.request.user.useraccount

        if not useraccount.is_tipster and not subscriber:
            raise BadRequestError(detail="subscriber query params is required.")

        if useraccount.is_tipster and not issuer:
            raise BadRequestError(detail="issuer query params is required.")

        if (useraccount.is_tipster and int(issuer) != int(useraccount.id)) or \
            (not useraccount.is_tipster and int(subscriber) != int(useraccount.id)):
            raise PermissionDeniedError(detail="You are not permitted to perform this action.")

        filterset = self.filter_class(
            data=query_params,
            queryset=Subscription.objects.all()
        )
        return filterset.qs

    def verify_subscription_permission(self, subscriber, tipster):
        if subscriber.is_tipster:
            raise SubscriptionError(
                detail='Subscription by Tipster not permitted',
            )

        if not tipster.is_tipster:
            raise SubscriptionError(
                detail='Subscription to non Tipster not permitted',
            )

    def verify_subscription(self, subscriber, tipster, **kwargs):
        period = kwargs.get('period')
        subscription_type = kwargs.get('subscription_type')
        self.verify_subscription_permission(subscriber, tipster)

        try:
            subscription = Subscription.objects.filter(
                subscriber=subscriber,
                issuer=tipster,
                is_active=True
            ).latest('subscription_date')
        except Subscription.DoesNotExist:
            return

        if subscription.type == Subscription.FREE and subscription_type == Subscription.FREE:
            raise SubscriptionError(
                detail='You\'ve already subscribed to Free plan',   
            )

        if subscription.type == Subscription.TRIAL:
            if period != tipster.pricing.trial_period:
                raise SubscriptionError(
                    detail='Incorrect Trial Period. Doesn\'t match with Tipster\'s Trial Period',
                )
            if subscription.expiration_date < datetime.utcnow().replace(tzinfo=pytz.UTC):
                raise SubscriptionError(
                    detail='You\'ve already completed your Trial plan',
                )
            elif subscription.expiration_date > datetime.utcnow().replace(tzinfo=pytz.UTC):
                raise SubscriptionError(
                    detail='You\'ve already subscribed to Trial plan',
                )
        elif subscription.type == Subscription.PREMIUM:
            if subscription.expiration_date > datetime.utcnow().replace(tzinfo=pytz.UTC):
                raise SubscriptionError(
                    detail='You\'ve already subscribed to Premium plan',
                )

    def record_payment(self, amount, tipster, period):
        payment = Payment.objects.create(
            price=amount,
            currency=tipster.currency,
            period=period
        )

        return payment

    def subscribe(self, request):
        subscription_type = request.data.get('type')
        tipster_id = request.data.get('tipster')
        period = request.data.get('period')
        amount = request.data.get('amount')
        subscriber = request.user.useraccount
        tipster = self.get_object(tipster_id)
        payment = None

        self.verify_subscription(
            subscriber,
            tipster,
            period=period,
            subscription_type=subscription_type
        )

        if subscription_type == Subscription.PREMIUM:
            payment = self.record_payment(amount, tipster, period)

        subscription = Subscription(
            type=subscription_type,
            issuer=tipster,
            subscriber=subscriber,
        )

        if period:
            subscription.period = period
            subscription.expiration_date = datetime.utcnow().replace(tzinfo=pytz.UTC) + timedelta(days=period)

        if payment is not None:
            subscription.payment = payment
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


@permission_classes((permissions.IsAuthenticated, TipsterPermission, IsOwnerOrReadOnly))
class UserPricingAPIView(APIView):

    def get_object(self, pk):
        try:
            return UserAccount.objects.select_related('user', 'pricing').get(pk=pk)
        except UserAccount.DoesNotExist:
            raise Http404

    def post(self, request, pk=None):
        data = request.data
        user_account = self.get_object(pk)
        self.check_object_permissions(request, user_account)
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


@permission_classes((permissions.IsAuthenticated, TipsterPermission, IsOwnerOrReadOnly))
class UserWalletAPIView(APIView):

    def get_object(self, pk):
        try:
            return UserAccount.objects.select_related('wallet').get(pk=pk)
        except UserAccount.DoesNotExist:
            raise Http404

    def post(self, request, pk=None):
        user_account = self.get_object(pk)
        self.check_object_permissions(request, user_account)

        res = SubAccount.create(
            business_name=user_account.full_name,
            settlement_bank=request.data.get('bank'),
            account_number=request.data.get('account_number'),
            percentage_charge=settings.PERCENTAGE_CHARGE
        )

        if res.get('status') == False:
            raise PaymentSetupError(detail=res.get('message'), code=400)

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
            if request.query_params.get('tipster'):
                return UserAccount.objects.select_related('user').get(
                    user__username=username,
                    is_tipster=True
                )
            return UserAccount.objects.select_related('user').get(user__username=username)
        except UserAccount.DoesNotExist:
            raise Http404

    def get_account_owner(self, request):
        user_account = UserAccount.objects.get(
            user=request.user.id
        )
        self.check_object_permissions(request, user_account)
        serializer = OwnerUserAccountSerializer(user_account)

        return Response(serializer.data)

    def get_user(self, request, username=None):
        data = self.get_object(username, request)
        serializer = UserAccountSerializer(data)
        return Response(serializer.data)

    def get_users(self, request, username=None):
        query_params = request.query_params
        filterset = self.filter_class(
            data=query_params,
            queryset=UserAccount.objects.filter(
                user__is_active=True,
                is_tipster=True
            ).exclude(
                user__first_name=None,
                user__last_name=None,
                country=None,
                bio=None,
                display_name=None
            )
        )
        serializer = UserAccountSerializer(filterset.qs, many=True)

        return Response(serializer.data)

    def update_user(self, request, username=None):
        user_account = self.get_object(username)
        self.check_object_permissions(request, user_account)
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

    def delete_user(self, request, username=None):
        """
        Deleting a user is not used for now
        """
        user_account = self.get_object(username)
        self.check_object_permissions(request, user_account)
        user = user_account.user
        #TODO: Make sure a tipster has no open subscriptions before deleting account
        user.delete()
        return Response({
            'message': 'User deleted Successfully'
        })


@permission_classes((permissions.IsAuthenticated, IsOwnerOrSubscriberReadOnly,))
class TipsAPIView(APIView):
    filter_class = TipsFilterSet

    def get_object(self, pk):
        try:
            return UserAccount.objects.select_related('user').get(pk=pk)
        except UserAccount.DoesNotExist:
            raise Http404

    def get(self, request, pk=None, format=None):
        user_account = self.get_object(pk)
        self.check_object_permissions(request, user_account)
        mt_queryset = None
        bc_queryset = None

        if not request.user.useraccount.is_tipster:
            subscriptions = Subscription.objects.filter(
                subscriber=request.user.useraccount.id,
                is_active=True
            )
            sub_issuers = subscriptions.values_list("issuer__id", flat=True)
            # free_sub_issuers = []
            # premium_sub_issuers = []
            # for subscription in subscriptions:
            #     if subscription.type == subscription.PREMIUM or subscription.type == subscription.TRIAL:
            #         premium_sub_issuers.append(subscriptions.values_list("issuer__id", flat=True))
            #     else:
            #         free_sub_issuers.append(subscriptions.values_list("issuer__id", flat=True))

            mt_queryset = MatchTips.objects.filter(issuer__in=sub_issuers)
            bc_queryset = BookingCodeTips.objects.filter(issuer__in=sub_issuers)

        query_params = request.query_params
        filterset = self.filter_class(
            data=query_params,
            queryset= mt_queryset if mt_queryset else MatchTips.objects.filter(issuer=pk)
        )
        match_tips_serializer = MatchTipsSerializer(filterset.qs, many=True)

        booking_code = bc_queryset if bc_queryset else BookingCodeTips.objects.filter(issuer=pk)
        booking_code_serializer = BookingCodeTipsSerializer(booking_code, many=True)

        return Response({
            "match_tips": match_tips_serializer.data,
            "booking_code_tips": booking_code_serializer.data
        })

    # def put(self, request, pk=None, format=None):
    #     #TODO: Make sure tips can only be updated before it's sent to subscribers
    #     tips =  Tips.objects.get(pk=pk)
    #     serializer = TipsSerializer(instance=tips, data=request.data, partial=True)
    #     serializer.is_valid(raise_exception=True)
    #     serializer.save()
    #     return Response({
    #         'message': 'Tips updated Successfully',
    #         'data': serializer.data
    #     })

    def post(self, request, pk=None, format=None):
        #TODO: Confirm the match is valid from probably an API before saving to the DB
        user_account = self.get_object(pk)
        self.check_object_permissions(request, user_account)
        data = request.data

        if data.get('bookie'):
            bc_serializer = BookingCodeTipsSerializer(data=data)
            bc_serializer.is_valid(raise_exception=True)
            bc_serializer.save()

            return Response({
                'message': 'Tips Created Successfully',
                'data': bc_serializer.data
            })

        if int(data.get('issuer')) != int(pk):
            raise exceptions.PermissionDenied()

        mt_serializer = MatchTipsSerializer(data=data)
        mt_serializer.is_valid(raise_exception=True)
        mt_serializer.save()
        return Response({
            'message': 'Tips Created Successfully',
            'data': mt_serializer.data
        })

    # def delete(self, request, pk, format=None):
    #     #TODO: Make sure tips can only be deleted before it's sent to subscribers
    #     try:
    #         tips = Tips.objects.get(pk=pk)
    #     except Tips.DoesNotExist:
    #         raise Http404
    #     tips.delete()
    #     return Response({
    #         'message': 'Tips deleted Successfully'
    #     })
