import json
import hashlib
from django.conf import settings
from rest_framework.decorators import permission_classes
from rest_framework import permissions
from rest_framework.viewsets import ModelViewSet
from rest_framework.response import Response
from rest_framework import status
from core.models.user import UserAccount
from core.models.transaction import Transaction


@permission_classes((permissions.AllowAny,))
class WebhookAPIView(ModelViewSet):

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
    
    def get_client_ip(request):
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip

    def paystack_webhook(self, request):
        event = request.data.get("event")
        PAYSTACK_IPS = ['52.31.139.75', '52.49.173.169', '52.214.14.220']
        is_verified_origin = self.get_client_ip(request) in PAYSTACK_IPS
        if is_verified_origin:
            #TODO: Handle more events
            if event == "charge.success":
                self.record_successful_deposit_transaction(request)
            elif event == "transfer.success":
                self.record_successful_withdrawal_transaction(request)
        return Response(status=status.HTTP_200_OK)