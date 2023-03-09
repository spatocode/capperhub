from django.contrib.auth.models import User
from rest_framework import serializers
from rest_framework.exceptions import ValidationError
from dj_rest_auth.registration.serializers import RegisterSerializer
from rest_framework_simplejwt.serializers import TokenObtainSerializer, RefreshToken, get_user_model
from rest_framework_simplejwt import serializers as sjwt_serializers
from django_countries.serializer_fields import CountryField
from core.models.user import UserAccount, Pricing, Wallet
from core.models.play import Play
from core.models.wager import SportsWager, SportsWagerChallenge
from core.models.games import SportsGame
from core.models.transaction import Currency, Transaction
from core.models.subscription import Subscription

class UserAccountRegisterSerializer(RegisterSerializer):
    username = serializers.CharField(required=False)
    first_name = serializers.CharField(required=False)
    last_name = serializers.CharField(required=False)
    display_name = serializers.CharField(required=True)
    email = serializers.EmailField(required=True)
    password1 = serializers.CharField(write_only=True, required=True)
    password2 = serializers.CharField(write_only=True, required=True)

    def get_cleaned_data(self):
        super(UserAccountRegisterSerializer, self).get_cleaned_data()

        return {
            'username': self.validated_data.get('username', ''),
            'first_name': self.validated_data.get('first_name', ''),
            'last_name': self.validated_data.get('last_name', ''),
            'display_name': self.validated_data.get('display_name', ''),
            'password1': self.validated_data.get('password1', ''),
            'password2': self.validated_data.get('password2', ''),
            'email': self.validated_data.get('email', ''),
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
    free_features = serializers.ListField(required=False)
    premium_features = serializers.ListField(required=False)
    class Meta:
        model = Pricing
        fields = '__all__'



class OwnerUserWalletSerializer(serializers.ModelSerializer):
    class Meta:
        model = Wallet
        fields = '__all__'


class OwnerUserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        exclude = ['password']


class OwnerUserAccountSerializer(serializers.ModelSerializer):
    user = OwnerUserSerializer()
    pricing = UserPricingSerializer()
    free_subscribers = serializers.ListField()
    premium_subscribers = serializers.ListField()
    subscription_issuers = serializers.ListField()
    full_name = serializers.CharField()
    wallet = OwnerUserWalletSerializer()
    country = CountryField(name_only=True)

    class Meta:
        model = UserAccount
        fields = '__all__'
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
    pricing = UserPricingSerializer()
    free_subscribers = serializers.ListField()
    premium_subscribers = serializers.ListField()
    subscription_issuers = serializers.ListField()
    country = CountryField(name_only=True)
    is_punter = serializers.BooleanField()
    currency = serializers.CharField(source="wallet.currency.code")

    class Meta:
        model = UserAccount
        exclude = ['ip_address', 'phone_number', 'email_verified']


class PlaySerializer(serializers.ModelSerializer):
    issuer = UserAccountSerializer()
    
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


class SportsGameSerializer(serializers.ModelSerializer):
    added_by = serializers.CharField(source="added_by.user.username")
    wager_count = serializers.IntegerField(read_only=True)

    class Meta:
        model = SportsGame
        fields = '__all__'


class SportsWagerSerializer(serializers.ModelSerializer):
    game = SportsGameSerializer()
    backer = UserAccountSerializer()
    layer = UserAccountSerializer()
    winner = UserAccountSerializer()

    def to_internal_value(self, data):
        new_data = data
        backer = UserAccount.objects.get(id=data.get("backer"))
        new_data['backer'] = backer
        return new_data

    def create(self, validated_data):
        sports_game = SportsGame.objects.get_or_create(
            type=validated_data.get("game").pop("type"),
            competition=validated_data.get("game").pop("competition"),
            home=validated_data.get("game").pop("home"),
            away=validated_data.get("game").pop("away"),
            match_day=validated_data.get("game").pop("match_day")
        )
        if sports_game[1]:
            sports_game[0].added_by = validated_data.get("backer")            
            sports_game[0].save()
        if sports_game[0].result:
            raise ValidationError(detail="Game no longer available for wager")
        return SportsWager.objects.create(
            game=sports_game[0],
            market=validated_data.get("market"),
            backer=validated_data.get("backer"),
            backer_option=validated_data.get("backer_option"),
            stake=validated_data.get("stake"),
        )

    class Meta:
        model = SportsWager
        exclude = ['transaction']


class SportsWagerChallengeSerializer(serializers.ModelSerializer):
    wager = SportsWagerSerializer()
    requestor = UserAccountSerializer()
    requestee = UserAccountSerializer()

    class Meta:
        model = SportsWagerChallenge
        fields = '__all__'


class TransactionSerializer(serializers.ModelSerializer):
    user = UserAccountSerializer()
    currency = CurrencySerializer()

    class Meta:
        model = Transaction
        fields = '__all__'
