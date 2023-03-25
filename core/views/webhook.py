import json
import hashlib
from django.conf import settings
from rest_framework.decorators import permission_classes
from rest_framework import permissions
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from core.models.user import UserAccount
from core.models.transaction import Transaction
from core.permissions import PaystackWebhookPermission


@permission_classes((permissions.AllowAny, PaystackWebhookPermission))
class PaystackWebhookAPIView(APIView):

    def record_successful_deposit_transaction(request):
        data = request.data.get("data")
        user = UserAccount.objects.select_related("wallet").get(user__email=data["customer"]["email"])
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
        hash = hashlib.new("sha512", secret.encode('utf-8'))
        hash.update(body_bytes)
        hash_digest = hash.hexdigest()
        return hash_digest == xps_header

    def post(self, request):
        event = request.data.get("event")
        #TODO: Handle more events
        if event == "charge.success":
            self.record_successful_deposit_transaction(request)
        elif event == "transfer.success":
            self.record_successful_withdrawal_transaction(request)
        return Response(status=status.HTTP_200_OK)


@permission_classes((permissions.AllowAny,))
class WhatsappWebhookAPIView(APIView):
    def get(self, request):
        if request.query_params.get('hub.verify_token') == settings.WHATSAPP_WEBHOOK_VERIFY_TOKEN:
            return Response(int(request.query_params.get('hub.challenge')))
        return Response(status=status.HTTP_403_FORBIDDEN)

    def post(self, request):
        return Response(status=status.HTTP_200_OK)
