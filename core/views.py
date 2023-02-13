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
from rest_framework_simplejwt.views import TokenObtainPairView
from core.permissions import IsOwnerOrReadOnly, IsOwnerOrSubscriberReadOnly
from core.serializers import (
    PlaySerializer, UserAccountSerializer, UserAccountRegisterSerializer,
    SubscriptionSerializer, UserPricingSerializer, OwnerUserAccountSerializer,
    OwnerUserSerializer, CustomTokenObtainPairSerializer, UserWalletSerializer,
)
from core.models.user import UserAccount
from core.models.transaction import Currency, Transaction
from core.models.play import Play
from core.models.subscription import Subscription
from core.filters import PlayFilterSet, UserAccountFilterSet, SubscriptionFilterSet
from core.exceptions import SubscriptionError, PricingError, PermissionDeniedError, BadRequestError


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
        transaction = Transaction.objects.create(
            type=Transaction.DEPOSIT,
            user=subscriber,
            issuer=kwargs.get('issuer'),
            channel=kwargs.get('channel'),
            price=kwargs.get('amount'),
            currency=kwargs.get('currency'),
            period=kwargs.get('period')
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

        if previous_subscription.type == Subscription.FREE and subscription_type == Subscription.PREMIUM:
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
class PlayAPIView(APIView):
    filter_class = PlayFilterSet

    def get_object(self, pk):
        try:
            return UserAccount.objects.select_related('user').get(pk=pk)
        except UserAccount.DoesNotExist:
            raise Http404

    def get(self, request, pk=None, format=None):
        issuer = self.get_object(pk)
        self.check_object_permissions(request, issuer)
        mt_queryset = None

        if not request.user.useraccount.is_tipster:
            subscriptions = Subscription.objects.filter(
                subscriber=request.user.useraccount.id,
                is_active=True
            )
            issuers = subscriptions.values_list("issuer__id", flat=True)
            import pdb; pdb.set_trace()

            mt_queryset = Play.objects.filter(issuer__in=issuers, )

        query_params = request.query_params
        filterset = self.filter_class(
            data=query_params,
            queryset= mt_queryset if mt_queryset else Play.objects.filter(issuer=pk)
        )
        play_serializer = PlaySerializer(filterset.qs, many=True)

        return Response({
            "plays": play_serializer.data
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

        if int(data.get('issuer')) != int(pk):
            raise exceptions.PermissionDenied()

        play_serializer = PlaySerializer(data=data)
        play_serializer.is_valid(raise_exception=True)
        play_serializer.save()
        return Response({
            'message': 'Play Created Successfully',
            'data': play_serializer.data
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
