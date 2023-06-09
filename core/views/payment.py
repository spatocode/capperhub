import requests
from django.conf import settings
from rest_framework.decorators import permission_classes
from rest_framework import permissions
from rest_framework.response import Response
from rest_framework import status
from rest_framework import viewsets
from rest_framework.views import APIView
from paystackapi.transaction import Transaction as PaystackTransaction
from paystackapi.verification import Verification
from paystackapi.misc import Misc as PaystackMisc
from paystackapi.trecipient import TransferRecipient
from paystackapi.transfer import Transfer
from python_flutterwave import payment
from rave_python import Rave, RaveExceptions, Misc
from core.permissions import IsOwnerOrReadOnly
from core.models.user import UserAccount
from core.models.transaction import Transaction
from core.serializers import TransactionSerializer
from core.exceptions import InsuficientFundError, NotFoundError
from core.shared.model_utils import generate_reference_code


payment.token = settings.RAVE_SECRET_KEY


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
                    currency=userwallet.currency,
                    reference=reference,
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
        response = PaystackMisc.list_banks(country=request.user.useraccount.country.name)
        return Response(response)

    def resolve_bank_details(self, request):
        response = Verification.verify_account(
            account_number=request.data.get("account_number"),
            bank_code=request.data.get("bank_code")
        )
        return Response(response)


@permission_classes((permissions.IsAuthenticated,))
class FlutterwavePaymentAPIView(viewsets.ModelViewSet):
    rave = Rave(settings.RAVE_PUBLIC_KEY, settings.RAVE_SECRET_KEY, production=settings.DEBUG)

    def list_banks(self, request):
        headers = {'Authorization': settings.RAVE_SECRET_KEY}
        url = f'https://api.flutterwave.com/v3/banks/{request.user.useraccount.country.code}'
        response = requests.get(url, headers=headers)
        return Response(response)

    def resolve_bank_account(self, request):
        headers = {'Authorization': settings.RAVE_SECRET_KEY}
        data = {
            "account_number": request.data.get("account_number"),
            "account_bank": request.data.get("bank_code")
        }
        url = 'https://api.flutterwave.com/v3/accounts/resolve'
        response = requests.get(url, headers=headers, json=data)
        return Response(response)

    def initialize_payment(self, request):
        useraccount = request.user.useraccount
        res = payment.initiate_payment(
            tx_ref=generate_reference_code(),
            amount=request.data.get('amount'),
            redirect_url=request.data.get("redirect_url"),
            customer_email=request.user.email,
            customer_phone_number=useraccount.phone_number,
            customer_name=useraccount.full_name,
        )
        if len(res) < 2 or res[1]["status"] != "success":
            return Response({"detail": "Error initiating payment"}, status=status.HTTP_403_FORBIDDEN)
        return Response({"message": "Payment initiated", "data": res[0]})

    def charge_card(self, request):
        try:
            payload = request.data.copy()
            chargeWithToken=payload.get("chargeWithToken")
            pin=request.payload.get("pin")
            address=request.payload.get("address")
            payload.pop("chargeWithToken")
            payload.pop("pin")
            payload.pop("address")
            payload["subaccounts"] = [{id: request.user.useraccount.wallet.meta["fw_subaccount_id"]}]
            if chargeWithToken:
                res = self.rave.Card.charge(request.data, chargeWithToken=chargeWithToken)
            else:
                res = self.rave.Card.charge(request.data)
            if res.get("suggestedAuth"):
                arg = Misc.getTypeOfArgsRequired(res.get("suggestedAuth"))
                if arg == "pin":
                    Misc.updatePayload(res.get("suggestedAuth"), request.data, pin=pin)
                if arg == "address":
                    Misc.updatePayload(res.get("suggestedAuth"), request.data, address=address)
                res = self.rave.Card.charge(request.data)
            return Response(res)
        except RaveExceptions.CardChargeError as e:
            return Response({"detail": e.err["errMsg"]}, status=status.HTTP_403_FORBIDDEN)
        except RaveExceptions.TransactionValidationError as e:
            return Response({"detail": e.err}, status=status.HTTP_403_FORBIDDEN)
        except RaveExceptions.TransactionVerificationError as e:
            return Response({"detail": e.err["errMsg"]}, status=status.HTTP_403_FORBIDDEN)

    def validate_charge(self, request):
        try:
            flwRef = request.data.get("flwRef")
            otp = request.data.get("otp")
            res = self.rave.Card.validate(flwRef, otp)
            return Response(res)
        except RaveExceptions.CardChargeError as e:
            return Response({"detail": e.err["errMsg"]}, status=status.HTTP_403_FORBIDDEN)

    def verify_charge(self, request):
        res = self.rave.Card.verify(request.data.get("txRef"))
        return Response(res)

    def initialize_payout(self, request):
        user = request.user.useraccount
        userwallet = user.wallet
        amount = request.data.get("amount")
        if userwallet.balance < int(amount):
            raise InsuficientFundError(detail="You don't have sufficient fund to withdraw")
        try:
            res = self.rave.Transfer.initiate({
                "account_bank": request.data.get("account_bank"),
                "account_number": request.data.get("account_number"),
                "amount": amount,
                "narration": "Predishun Systems Ltd. Payout",
                "currency": userwallet.currency.code,
                "beneficiary_name": request.user.useraccount.full_name
            })
            return Response(res)
        except RaveExceptions.IncompletePaymentDetailsError as e:
            import pdb; pdb.set_trace()
            return Response({"detail": e})
