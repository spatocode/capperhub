from rest_framework.decorators import permission_classes
from rest_framework import permissions
from rest_framework.response import Response
from rest_framework import status
from rest_framework import viewsets
from rest_framework.views import APIView
from paystackapi.transaction import Transaction as PaystackTransaction
from paystackapi.verification import Verification
from paystackapi.misc import Misc
from paystackapi.trecipient import TransferRecipient
from paystackapi.transfer import Transfer
from core.permissions import IsOwnerOrReadOnly
from core.models.user import UserAccount
from core.models.transaction import Transaction
from core.serializers import TransactionSerializer
from core.exceptions import InsuficientFundError, NotFoundError
from core.shared.model_utils import generate_reference_code


@permission_classes((permissions.IsAuthenticated, IsOwnerOrReadOnly))
class PaymentTransactionAPIView(APIView):
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
class PaystackPaymentAPIView(viewsets.ModelViewSet):
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


@permission_classes((permissions.IsAuthenticated,))
class FlutterwavePaymentAPIView(viewsets.ModelViewSet):
    def list_banks(self, request):
        pass

    def resolve_bank_account(self, request):
        pass

    def charge_card(self, request):
        pass

    def validate_charge(self, request):
        pass

    def verify_charge(self, request):
        pass

    def initialize_payout(self, request):
        pass
