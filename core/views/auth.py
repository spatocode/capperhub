from dj_rest_auth.registration.views import RegisterView
from core.serializers import UserAccountRegisterSerializer
from core.models.user import Wallet, Pricing
from core.models.transaction import Currency


class UserAccountRegisterView(RegisterView):
    serializer_class = UserAccountRegisterSerializer

    def perform_create(self, serializer):
        user = super().perform_create(serializer)
        user_account = user.useraccount
        user_account.display_name = serializer.data.get('display_name')
        user_account.country = serializer.data.get('country')
        wallet = Wallet.objects.create(currency=Currency.objects.get(country=user_account.country))
        pricing = Pricing.objects.create()
        user_account.wallet = wallet
        user_account.pricing = pricing
        user_account.save()
        return user