import pytz
from datetime import datetime, timedelta
from django.conf import settings
from django.core.cache import cache
from rest_framework.decorators import permission_classes
from rest_framework import permissions
from rest_framework.views import APIView
from rest_framework import viewsets, parsers
from rest_framework.response import Response
from core.permissions import IsOwnerOrReadOnly
from core.serializers import (
    UserAccountSerializer, UserPricingSerializer, OwnerUserAccountSerializer,
    OwnerUserSerializer
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

    def get_account_owner(self, request):
        user_account = UserAccount.objects.get(
            user=request.user.id,
            user__is_active=True
        )
        self.check_object_permissions(request, user_account.id)
        serializer = OwnerUserAccountSerializer(user_account)
        data = serializer.data

        return Response(data)
    
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

    def get_user(self, request, username=None):
        data = self.get_object(username)
        serializer = UserAccountSerializer(data)
        return Response(serializer.data)


@permission_classes((permissions.IsAuthenticated,))
class UserPricingAPIView(APIView):

    def post(self, request, format=None):
        user_account = request.user.useraccount
        # Make sure pricing can be updated once in 60days
        if user_account.pricing and float(request.data.get("amount")) != user_account.pricing.amount:
            date_due_for_update = user_account.pricing.last_update + timedelta(days=60)
            if date_due_for_update > datetime.utcnow().replace(tzinfo=pytz.UTC):
                raise PricingError(
                    detail='Pricing can only be updated once in 60 days',
                    code=403
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
