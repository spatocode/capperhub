from dj_rest_auth.registration.views import RegisterView
from core.serializers import UserAccountRegisterSerializer
from core.models.user import Wallet, Pricing, UserAccount
from core.models.transaction import Currency


class UserAccountRegisterView(RegisterView):
    serializer_class = UserAccountRegisterSerializer

    def perform_create(self, serializer):
        user = super().perform_create(serializer)
        try:
            currency = Currency.objects.get(country=serializer.data.get('country'))
        except Currency.DoesNotExist:
            currency = Currency.objects.get(country="US")
        wallet = Wallet.objects.create(currency=currency)
        pricing = Pricing.objects.create()
        user_account = UserAccount.objects.create(user=user, wallet=wallet, pricing=pricing)
        user_account.display_name = serializer.data.get('display_name')
        user_account.country = serializer.data.get('country')
        user_account.save()
        return user