from django.contrib.auth.models import User
from rest_framework import serializers
from dj_rest_auth.registration.serializers import RegisterSerializer
from django_countries.serializers import CountryFieldMixin
from core.models.user import UserAccount, Pricing
from core.models.tips import Tips
from core.models.currency import Currency
from core.models.subscription import Subscription, Payment

class UserAccountRegisterSerializer(RegisterSerializer):
    username = serializers.CharField(required=True)
    first_name = serializers.CharField(required=True)
    last_name = serializers.CharField(required=True)
    email = serializers.EmailField(required=True)
    password1 = serializers.CharField(write_only=True, required=True)
    password2 = serializers.CharField(write_only=True, required=True)
    phone_number = serializers.CharField(required=False)
    is_tipster = serializers.BooleanField(required=False)

    def get_cleaned_data(self):
        super(UserAccountRegisterSerializer, self).get_cleaned_data()

        return {
            'username': self.validated_data.get('username', ''),
            'first_name': self.validated_data.get('first_name', ''),
            'last_name': self.validated_data.get('last_name', ''),
            'password1': self.validated_data.get('password1', ''),
            'password2': self.validated_data.get('password2', ''),
            'email': self.validated_data.get('email', ''),
            'cell_phone': self.validated_data.get('phone_number', ''),
            'is_tipster': self.validated_data.get('is_tipster', ''),
        }


class UserPricingSerializer(serializers.ModelSerializer):
    class Meta:
        model = Pricing
        fields = '__all__'


class OwnerUserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        exclude = ['password']


class OwnerUserAccountSerializer(CountryFieldMixin, serializers.ModelSerializer):
    user = OwnerUserSerializer()
    pricing = UserPricingSerializer()

    class Meta:
        model = UserAccount
        fields = '__all__'


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'username', 'email']


class UserAccountSerializer(CountryFieldMixin, serializers.ModelSerializer):
    user = UserSerializer()

    class Meta:
        model = UserAccount
        exclude = ['ip_address', 'phone_number', 'email_verified']


class TipsSerializer(serializers.ModelSerializer):

    def validate_issuer(self, value):
        """
        Check that the owner is a tipster
        """
        user_account = value
        if not user_account.is_tipster:
            raise serializers.ValidationError("Only Tipsters can create tips")
        return value

    class Meta:
        model = Tips
        fields = '__all__'
        read_only_fields = ['id']


class CurrencySerializer(serializers.ModelSerializer):
    class Meta:
        model = Currency
        fields = '__all__'


class PaymentSerializer(serializers.ModelSerializer):
    base_currency = CurrencySerializer()
    payment_currency = CurrencySerializer()

    class Meta:
        model = Payment
        fields = '__all__'


class SubscriptionSerializer(serializers.ModelSerializer):
    issuer = UserAccountSerializer()
    subscriber = UserAccountSerializer()
    payment = PaymentSerializer()

    class Meta:
        model = Subscription
        fields = '__all__'
