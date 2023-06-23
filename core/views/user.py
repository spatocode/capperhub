import pytz
from datetime import datetime, timedelta
from django.conf import settings
from django.core.cache import cache
from django_ratelimit.decorators import ratelimit
from django.utils.decorators import method_decorator
from rest_framework.decorators import permission_classes
from rest_framework import status
from rest_framework import permissions
from rest_framework.views import APIView
from rest_framework import viewsets, parsers
from rest_framework.response import Response
from rave_python import Rave, RaveExceptions
from core.permissions import IsOwnerOrReadOnly
from core.serializers import (
    UserAccountSerializer, UserPricingSerializer, OwnerUserAccountSerializer,
    OwnerUserSerializer, OwnerUserWalletSerializer
)
from core.models.user import UserAccount
from core.filters import UserAccountFilterSet
from core.exceptions import PricingError, NotFoundError


@permission_classes((permissions.AllowAny, IsOwnerOrReadOnly))
class UserAccountOwnerAPIView(viewsets.ModelViewSet):
    filter_class = UserAccountFilterSet

    def get_object(self, username):
        try:
            return UserAccount.objects.select_related('user').get(user__username=username, user__is_active=True)
        except UserAccount.DoesNotExist:
            raise NotFoundError(detail="User not found")

    @method_decorator(ratelimit(key='ip', rate=f'{settings.DEFAULT_RATE_LIMIT}/m', method='GET'))
    def get_account_owner(self, request):
        user_account = UserAccount.objects.get(
            user=request.user.id,
            user__is_active=True
        )
        self.check_object_permissions(request, user_account.id)
        serializer = OwnerUserAccountSerializer(user_account)
        data = serializer.data

        return Response(data)

    @method_decorator(ratelimit(key='ip', rate=f'{settings.DEFAULT_RATE_LIMIT}/m', method='PUT'))
    def update_user(self, request, username=None):
        user_serializer = OwnerUserSerializer(
            instance=request.user,
            data=request.data,
            partial=True
        )
        user_serializer.is_valid(raise_exception=True)
        user_serializer.save()

        serializer = OwnerUserAccountSerializer(
            instance=request.user.useraccount,
            data=request.data,
            partial=True
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        data = serializer.data
        cache_key = f'{request.user.useraccount.id}_owner'
        cache.set(cache_key, data, timeout=settings.CACHE_TTL)
        return Response({
            'message': 'User updated Successfully',
            'data': data
        })


@permission_classes((permissions.AllowAny, IsOwnerOrReadOnly))
class UserAPIView(viewsets.ModelViewSet):
    filter_class = UserAccountFilterSet
    parser_classes = [parsers.MultiPartParser, parsers.FormParser]

    def get_object(self, username):
        try:
            return UserAccount.objects.select_related('user').get(user__username=username, user__is_active=True)
        except UserAccount.DoesNotExist:
            raise NotFoundError(detail="User not found")

    @method_decorator(ratelimit(key='ip', rate=f'{settings.DEFAULT_RATE_LIMIT}/m', method='GET'))
    def get_user(self, request, username=None):
        data = self.get_object(username)
        serializer = UserAccountSerializer(data)
        return Response(serializer.data)


@permission_classes((permissions.IsAuthenticated,))
class UserPricingAPIView(APIView):

    @method_decorator(ratelimit(key='ip', rate=f'{settings.DEFAULT_RATE_LIMIT}/m', method='POST'))
    def post(self, request, format=None):
        user_account = request.user.useraccount
        # Make sure pricing can be updated once in 60days
        if user_account.pricing and float(request.data.get("amount")) != user_account.pricing.amount:
            date_due_for_update = user_account.pricing.last_update + timedelta(days=60)
            if (user_account.pricing.created_at.replace(microsecond=0) != user_account.pricing.last_update.replace(microsecond=0)) \
                and date_due_for_update > datetime.utcnow().replace(tzinfo=pytz.UTC):
                raise PricingError(
                    detail='Pricing can only be updated once in 60 days',
                    code=403
                )
        if not user_account.pricing:
            serializer = UserPricingSerializer(data=request.data)
        else:
            serializer = UserPricingSerializer(instance=user_account.pricing, data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response({
            'message': 'User Pricing Added Successfully',
            'data': serializer.data
        })

@permission_classes((permissions.IsAuthenticated,))
class UserPaymentDetailsAPIView(APIView):
    rave = Rave(settings.RAVE_PUBLIC_KEY, settings.RAVE_SECRET_KEY, production=True)

    def create_subaccount(self, user_account, data):
        try:
            res = self.rave.SubAccount.create({
                "country": user_account.country.code,
                "account_bank": data.get("bank_code"),
                "account_number": data.get("bank_account_number"),
                "business_name": data.get("account_name"),
                "business_email": user_account.user.email,
                "business_contact": data.get("account_name"),
                "business_contact_mobile": user_account.phone_number,
                "business_mobile": user_account.phone_number,
                "split_type": "percentage",
                "split_value": settings.PERCENTAGE_CHARGE,
                # "meta": [{"metaname": "MarketplaceID", "metavalue": "ggs-920900"}]
            })
            if not res.get('error'):
                user_account.wallet.meta['fw_subaccount_id'] = res['data']['subaccount_id']
                user_account.wallet.save()
        except RaveExceptions.SubaccountCreationError as e:
            return e.err["errMsg"]

    @method_decorator(ratelimit(key='ip', rate=f'{settings.DEFAULT_RATE_LIMIT}/m', method='POST'))
    def post(self, request, format=None):
        user_account = request.user.useraccount
        # Make sure pricing can be updated once in 60days
        if user_account.wallet.bank_code and user_account.wallet.bank_account_number:
            raise PricingError(
                detail='Bank details cannot be updated',
                code=403
            )
        err = self.create_subaccount(user_account, request.data)
        if err:
            return Response({"detail": err}, status=status.HTTP_403_FORBIDDEN)

        name = request.data.get("account_name")
        split_name = name.split()
        request.user.first_name = split_name[0]
        if len(split_name) > 1:
            request.user.last_name = split_name[1:]
        request.user.save()

        serializer = OwnerUserWalletSerializer(instance=user_account.wallet, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response({
            'message': 'User Payment Details Added Successfully',
            'data': serializer.data
        })
