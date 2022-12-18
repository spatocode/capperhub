import pytz
from datetime import datetime, timedelta
from django.http.response import Http404
from rest_framework.decorators import permission_classes
from rest_framework import authentication, permissions
from rest_framework.views import APIView
from rest_framework.viewsets import ModelViewSet
from rest_framework.response import Response
from rest_framework.exceptions import APIException
from dj_rest_auth.registration.views import RegisterView
from core.permissions import BettorPermission, TipsterPermission, IsOwnerOrReadOnly
from core.serializers import (
    TipsSerializer, UserAccountSerializer, UserAccountRegisterSerializer,
    SubscriptionSerializer, UserPricingSerializer, OwnerUserAccountSerializer,
    OwnerUserSerializer, UserSerializer
)
from core.models.user import UserAccount
from core.models.tips import Tips
from core.models.subscription import Subscription, Payment
from core.filters import TipsFilterSet, UserAccountFilterSet, SubscriptionFilterSet
from core.exceptions import SubscriptionError, PricingError


class CsrfExemptSessionAuthentication(authentication.SessionAuthentication):
    def enforce_csrf(self, request):
        return


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


@permission_classes((permissions.IsAuthenticated, BettorPermission, IsOwnerOrReadOnly))
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
            ).latest('date_initialized')
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
            if subscription.date_expired < datetime.utcnow().replace(tzinfo=pytz.UTC):
                raise SubscriptionError(
                    detail='You\'ve already completed your Trial plan',
                )
            elif subscription.date_expired > datetime.utcnow().replace(tzinfo=pytz.UTC):
                raise SubscriptionError(
                    detail='You\'ve already subscribed to Trial plan',
                )
        elif subscription.type == Subscription.PREMIUM:
            if subscription.date_expired > datetime.utcnow().replace(tzinfo=pytz.UTC):
                raise SubscriptionError(
                    detail='You\'ve already subscribed to Premium plan',
                )

    def make_payment(self, tipster, subscriber, **kwargs):
        period = kwargs.get('period')
        price = tipster.pricing.amount
        # Add discount if period is more than a month
        if period > 30:
            discount = tipster.pricing.percentage_discount
            price = price - (price * discount)
        subscriber_currency = subscriber.currency
        tipster_currency = tipster.currency
        payment_price = price
        if tipster_currency.id != subscriber_currency.id:
            # TODO: Use currency API service to get/convert the subscriber 
            # currency to tipster currency thereby changing payment price
            pass

        payment = Payment.objects.create(
            base_price=price,
            base_currency=tipster_currency,
            payment_currency=subscriber_currency,
            payment_price=payment_price
        )

        return payment

    def subscribe(self, request, pk=None):
        subscription_type = request.data.get('type')
        tipster_id = request.data.get('tipster')
        period = request.data.get('period')
        subscriber = self.get_object(pk)
        tipster = self.get_object(tipster_id)
        payment = None

        self.verify_subscription(
            subscriber,
            tipster,
            period=period,
            subscription_type=subscription_type
        )

        if subscription_type == Subscription.TRIAL:
            #TODO: Add credit card before commencing on trial
            pass

        if subscription_type == Subscription.PREMIUM:
            payment = self.make_payment(tipster, subscriber, period=period)

        subscription = Subscription(
            type=subscription_type,
            issuer=tipster,
            subscriber=subscriber,
            period=period,
            date_expired=datetime.utcnow().replace(tzinfo=pytz.UTC) + timedelta(days=period)
        )
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
        subscriber = self.get_object(pk)
        tipster = self.get_object(tipster_id)

        self.verify_subscription_permission(subscriber, tipster)
        try:
            subscription = Subscription.objects.filter(
                subscriber=subscriber,
                issuer=tipster,
                is_active=True
            ).latest('date_initialized')
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
            return UserAccount.objects.get(pk=pk)
        except UserAccount.DoesNotExist:
            raise Http404

    def post(self, request, pk=None):
        data = request.data
        user_account = UserAccount.objects.select_related('user', 'pricing').get(pk=pk)
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


@permission_classes((permissions.AllowAny, IsOwnerOrReadOnly))
class UserAPIView(ModelViewSet):
    filter_class = UserAccountFilterSet

    def get_object(self, username):
        try:
            return UserAccount.objects.get(user__username=username)
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
        data = self.get_object(username)
        serializer = UserAccountSerializer(data)
        return Response(serializer.data)
    
    def get_users(self, request, username=None):
        query_params = request.query_params
        filterset = self.filter_class(
            data=query_params,
            queryset=UserAccount.objects.filter(
                user__is_active=True,
                is_tipster=True
            )
        )
        serializer = UserAccountSerializer(filterset.qs, many=True)

        return Response(serializer.data)
    
    def update_user(self, request, username=None):
        user_account = UserAccount.objects.select_related('user').get(user__username=username)
        self.check_object_permissions(request, user_account)
        user_serializer = OwnerUserSerializer(
            instance=user_account.user,
            data=request.data,
            partial=True
        )
        user_serializer.is_valid(raise_exception=True)
        user_serializer.save()
        
        serializer = OwnerUserAccountSerializer(
            instance=user_account,
            data=request.data,
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
        user_account = UserAccount.objects.select_related('user').get(user__username=username)
        self.check_object_permissions(request, user_account)
        user = user_account.user
        #TODO: Make sure a tipster has no open subscriptions before deleting account
        user.delete()
        return Response({
            'message': 'User deleted Successfully'
        })


@permission_classes((permissions.IsAuthenticated, TipsterPermission))
class TipsAPIView(APIView):
    filter_class = TipsFilterSet

    def get_object(self, pk):
        try:
            return Tips.objects.get(pk=pk)
        except Tips.DoesNotExist:
            raise Http404

    def get(self, request, pk=None, format=None):
        if pk:
            data = self.get_object(pk)
            serializer = TipsSerializer(data)
        else:
            query_params = request.query_params
            filterset = self.filter_class(
                data=query_params,
                queryset=Tips.objects.all()
            )
            serializer = TipsSerializer(filterset.qs, many=True)

        return Response(serializer.data)

    def put(self, request, pk=None, format=None):
        #TODO: Make sure tips can only be updated before it's sent to subscribers
        tips =  Tips.objects.get(pk=pk)
        serializer = TipsSerializer(instance=tips, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response({
            'message': 'Tips updated Successfully',
            'data': serializer.data
        })

    def post(self, request, format=None):
        #TODO: Confirm the match is valid from probably an API before saving to the DB
        data = request.data
        serializer = TipsSerializer(data=data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response({
            'message': 'Tips Created Successfully',
            'data': serializer.data
        })

    def delete(self, request, pk, format=None):
        #TODO: Make sure tips can only be deleted before it's sent to subscribers
        try:
            tips = Tips.objects.get(pk=pk)
        except Tips.DoesNotExist:
            raise Http404
        tips.delete()
        return Response({
            'message': 'Tips deleted Successfully'
        })
