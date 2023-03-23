import pytz
from datetime import datetime, timedelta
from django.conf import settings
from django.core.cache import cache
from django.core.cache.backends.base import DEFAULT_TIMEOUT
from rest_framework.decorators import permission_classes
from rest_framework import permissions
from rest_framework.views import APIView
from rest_framework.viewsets import ModelViewSet
from rest_framework.response import Response
from rest_framework import status
from paystackapi.transaction import Transaction as PaystackTransaction
from paystackapi.verification import Verification
from paystackapi.misc import Misc
from paystackapi.trecipient import TransferRecipient
from paystackapi.transfer import Transfer
from core.permissions import IsOwnerOrReadOnly
from core.serializers import (
    UserAccountSerializer, UserPricingSerializer, OwnerUserAccountSerializer,
    OwnerUserSerializer, OwnerUserWalletSerializer
)
from core.models.user import UserAccount
from core.models.transaction import Transaction
from core.filters import UserAccountFilterSet
from core.exceptions import PricingError, InsuficientFundError, NotFoundError
from core.shared.model_utils import generate_reference_code

@permission_classes((permissions.AllowAny, IsOwnerOrReadOnly))
class UserAccountOwnerAPIView(ModelViewSet):
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


@permission_classes((permissions.AllowAny, IsOwnerOrReadOnly))
class UserAPIView(ModelViewSet):
    filter_class = UserAccountFilterSet

    def get_object(self, username):
        try:
            return UserAccount.objects.select_related('user').get(user__username=username, user__is_active=True)
        except UserAccount.DoesNotExist:
            raise NotFoundError(detail="User not found")

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
        data = serializer.data
        cache_key = f'{request.user.useraccount.id}_owner'
        cache.set(cache_key, data, timeout=settings.CACHE_TTL)
        return Response({
            'message': 'User updated Successfully',
            'data': data
        })


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
        name = request.data.get("name")
        tr_response = TransferRecipient.create(
            type=type,
            name=name,
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
                reason="Predishun Withdrawal",
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
                splited_name = name.split(' ')
                if len(splited_name) > 1:
                    first_name = splited_name[0]
                    last_name = splited_name[1:]
                    request.user.first_name = first_name
                    request.user.last_name = last_name
                    request.user.save()
                else:
                    request.user.first_name = name
                    request.user.save()
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

