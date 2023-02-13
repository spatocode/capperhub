from django.contrib.auth.models import User
from rest_framework import serializers
from rest_framework.exceptions import ValidationError
from dj_rest_auth.registration.serializers import RegisterSerializer
from rest_framework_simplejwt.serializers import TokenObtainSerializer, RefreshToken, get_user_model
from rest_framework_simplejwt import serializers as sjwt_serializers
from django_countries.serializer_fields import CountryField
from core.models.user import UserAccount, Pricing, Wallet
from core.models.play import Play
from core.models.transaction import Currency, Transaction
from core.models.subscription import Subscription

class UserAccountRegisterSerializer(RegisterSerializer):
    username = serializers.CharField(required=False)
    first_name = serializers.CharField(required=False)
    last_name = serializers.CharField(required=False)
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


class EmailTokenObtainSerializer(TokenObtainSerializer):
    username_field = get_user_model().EMAIL_FIELD

    def __init__(self, *args, **kwargs):
        super(EmailTokenObtainSerializer, self).__init__(*args, **kwargs)
        self.fields[self.username_field] = serializers.CharField()
        self.fields['password'] = sjwt_serializers.PasswordField()

    def validate(self, attrs):
        # self.user = authenticate(**{
        #     self.username_field: attrs[self.username_field],
        #     'password': attrs['password'],
        # })
        self.user = User.objects.filter(email=attrs[self.username_field]).first()

        if not self.user:
            raise ValidationError('The user is not valid.')

        if self.user:
            if not self.user.check_password(attrs['password']):
                raise ValidationError('Incorrect credentials.')
        # Prior to Django 1.10, inactive users could be authenticated with the
        # default `ModelBackend`. As of Django 1.10, the `ModelBackend`
        # prevents inactive users from authenticating.  App designers can still
        # allow inactive users to authenticate by opting for the new
        # `AllowAllUsersModelBackend`. However, we explicitly prevent inactive
        # users from authenticating to enforce a reasonable policy and provide
        # sensible backwards compatibility with older Django versions.
        if self.user is None or not self.user.is_active:
            raise ValidationError('No active account found with the given credentials')

        return {}

    @classmethod
    def get_token(cls, user):
        raise NotImplemented(
            'Must implement `get_token` method for `MyTokenObtainSerializer` subclasses')


class CustomTokenObtainPairSerializer(EmailTokenObtainSerializer):
    @classmethod
    def get_token(cls, user):
        return RefreshToken.for_user(user)

    def validate(self, attrs):
        data = super().validate(attrs)

        refresh = self.get_token(self.user)

        data["refresh"] = str(refresh)
        data["access"] = str(refresh.access_token)

        return data


class UserPricingSerializer(serializers.ModelSerializer):
    class Meta:
        model = Pricing
        fields = '__all__'



class UserWalletSerializer(serializers.ModelSerializer):
    class Meta:
        model = Wallet
        exclude = ['balance']


class OwnerUserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        exclude = ['password']


class OwnerUserAccountSerializer(serializers.ModelSerializer):
    user = OwnerUserSerializer()
    pricing = UserPricingSerializer()
    subscriber_count = serializers.IntegerField()
    subscription_count = serializers.IntegerField()
    wallet = UserWalletSerializer()
    country = CountryField(name_only=True)

    class Meta:
        model = UserAccount
        exclude = ['currency']
        extra_kwargs = {
            'bio': {
                'required': False,
            }
        }


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'username', 'email']


class UserAccountSerializer(serializers.ModelSerializer):
    user = UserSerializer()
    full_name = serializers.CharField()
    pricing = UserPricingSerializer()
    subscriber_count = serializers.IntegerField()
    country = CountryField(name_only=True)

    class Meta:
        model = UserAccount
        exclude = ['ip_address', 'phone_number', 'email_verified']


class PlaySerializer(serializers.ModelSerializer):
    issuer = UserAccountSerializer()

    def validate_issuer(self, value):
        """
        Check that the owner is a tipster
        """
        user_account = value
        if not user_account.is_tipster:
            raise serializers.ValidationError("Only Tipsters can create tips")
        return value
    
    def to_internal_value(self, data):
        new_data = data
        issuer = UserAccount.objects.get(id=data.get("issuer"))
        new_data['issuer'] = issuer
        return new_data

    class Meta:
        model = Play
        fields = '__all__'
        read_only_fields = ['id']


class CurrencySerializer(serializers.ModelSerializer):
    class Meta:
        model = Currency
        fields = '__all__'


class TransactionSerializer(serializers.ModelSerializer):
    currency = CurrencySerializer()

    class Meta:
        model = Transaction
        fields = '__all__'


class SubscriptionSerializer(serializers.ModelSerializer):
    issuer = UserAccountSerializer()
    subscriber = UserAccountSerializer()

    class Meta:
        model = Subscription
        fields = '__all__'
