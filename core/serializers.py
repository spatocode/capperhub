from django.conf import settings
from django.contrib.auth.models import User
from django.contrib.auth.tokens import default_token_generator
from django.contrib.sites.shortcuts import get_current_site
from django.urls.base import reverse
from rest_framework import serializers
from rest_framework.exceptions import ValidationError
from dj_rest_auth.registration.serializers import RegisterSerializer
from rest_framework_simplejwt.serializers import TokenObtainSerializer, RefreshToken, get_user_model
from rest_framework_simplejwt import serializers as sjwt_serializers
from django_countries.serializer_fields import CountryField
from allauth.account import app_settings
from allauth.account.adapter import get_adapter
from allauth.account.utils import user_pk_to_url_str, user_username
from dj_rest_auth.forms import AllAuthPasswordResetForm
from dj_rest_auth.serializers import PasswordResetSerializer
from core.models.user import UserAccount, Pricing, Wallet
from core.models.play import Play, PlaySlip, Match
from core.models.wager import SportsWager, SportsWagerChallenge
from core.models.games import SportsGame, Team, Sport, Competition, Market
from core.models.transaction import Currency, Transaction
from core.models.subscription import Subscription
from core.models.misc import TermsOfUse, PrivacyPolicy, Feedback, Waitlist

class UserAccountRegisterSerializer(RegisterSerializer):
    username = serializers.CharField(required=False)
    display_name = serializers.CharField(required=True)
    email = serializers.EmailField(required=True)
    country = CountryField(required=True)
    password1 = serializers.CharField(write_only=True, required=True)
    password2 = serializers.CharField(write_only=True, required=True)

    def get_cleaned_data(self):
        super(UserAccountRegisterSerializer, self).get_cleaned_data()
        return {
            'username': self.validated_data.get('username', ''),
            'display_name': self.validated_data.get('display_name', ''),
            'password1': self.validated_data.get('password1', ''),
            'password2': self.validated_data.get('password2', ''),
            'email': self.validated_data.get('email', ''),
            'country': self.validated_data.get('country', ''),
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
    facebook = serializers.CharField(required=False, allow_blank=True)
    twitter = serializers.CharField(required=False, allow_blank=True)
    instagram = serializers.CharField(required=False, allow_blank=True)
    wallet = OwnerUserWalletSerializer()
    country = CountryField(name_only=True)
    image = serializers.ImageField(required=False)

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
    is_premium_capper = serializers.SerializerMethodField()
    fw_subaccount_id = serializers.SerializerMethodField()

    def get_is_premium_capper(self, instance):
        return instance.wallet.bank_code and instance.wallet.bank_account_number \
        and instance.pricing.amount and instance.pricing.amount > 0
    
    def get_fw_subaccount_id(self, instance):
        return instance.wallet.meta.get("fw_subaccount_id")

    class Meta:
        model = UserAccount
        exclude = ['ip_address', 'phone_number']


class PlaySlipSerializer(serializers.ModelSerializer):
    issuer = UserAccountSerializer()
    plays = serializers.SerializerMethodField(read_only=True)

    def get_plays(self, instance):
        serializer = PlaySerializer(data=instance.play_set.all(), many=True)
        serializer.is_valid()
        return serializer.data

    class Meta:
        model = PlaySlip
        fields = '__all__'
        read_only_fields = ('plays',)


class MatchSerializer(serializers.ModelSerializer):

    class Meta:
        model = Match
        fields = '__all__'


class PlaySerializer(serializers.ModelSerializer):
    match = MatchSerializer()

    class Meta:
        model = Play
        fields = '__all__'


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


class SportSerializer(serializers.ModelSerializer):

    class Meta:
        model = Sport
        fields = '__all__'


class SportsGameSerializer(serializers.ModelSerializer):
    type = SportSerializer()
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
        sport = Sport.objects.get(name=validated_data.get("game").pop("type"))
        sports_game = SportsGame.objects.get_or_create(
            type=sport,
            competition=validated_data.get("game").pop("competition"),
            home=validated_data.get("game").pop("home"),
            away=validated_data.get("game").pop("away"),
            match_day=validated_data.get("game").pop("match_day")
        )
        if sports_game[0].result:
            raise ValidationError(detail="Game no longer available for wager")
        transaction = Transaction.objects.create(
            type=Transaction.WAGER,
            amount=validated_data.get("stake"),
            balance=validated_data.get("backer").wallet.balance,
            user=validated_data.get("backer"),
            status=Transaction.PENDING,
            currency=validated_data.get("backer").wallet.currency
        )
        sports_wager = SportsWager.objects.create(
            game=sports_game[0],
            market=validated_data.get("market"),
            backer=validated_data.get("backer"),
            backer_option=validated_data.get("backer_option"),
            stake=validated_data.get("stake"),
            transaction=transaction,
        )
        sports_game[0].is_wager_played = True
        sports_game[0].save()
        return sports_wager

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


class TeamSerializer(serializers.ModelSerializer):

    class Meta:
        model = Team
        fields = '__all__'


class CompetitionSerializer(serializers.ModelSerializer):

    class Meta:
        model = Competition
        fields = '__all__'


class MarketSerializer(serializers.ModelSerializer):

    class Meta:
        model = Market
        fields = '__all__'


class PrivacyPolicySerializer(serializers.ModelSerializer):

    class Meta:
        model = PrivacyPolicy
        fields = '__all__'


class TermsOfUseSerializer(serializers.ModelSerializer):

    class Meta:
        model = TermsOfUse
        fields = '__all__'


class WaitlistSerializer(serializers.ModelSerializer):

    class Meta:
        model = Waitlist
        fields = '__all__'


class FeedbackSerializer(serializers.ModelSerializer):

    class Meta:
        model = Feedback
        fields = '__all__'


class CustomAllAuthPasswordResetForm(AllAuthPasswordResetForm):
    def save(self, request, **kwargs):
        current_site = get_current_site(request)
        email = self.cleaned_data['email']
        token_generator = kwargs.get('token_generator', default_token_generator)

        for user in self.users:

            temp_key = token_generator.make_token(user)

            # save it to the password reset model
            # password_reset = PasswordReset(user=user, temp_key=temp_key)
            # password_reset.save()

            # send the password reset email
            path = reverse(
                'password_reset_confirm',
                args=[user_pk_to_url_str(user), temp_key],
            )
            splitedPath = path.split('/')
            token = splitedPath[len(splitedPath) - 1]
            uid = splitedPath[len(splitedPath) - 2]
            # url = build_absolute_uri(None, path) # PASS NONE INSTEAD OF REQUEST
            url = settings.CLIENT_RESET_PASSWORD_URL + '/' + uid + '/' + token
            context = {
                'current_site': current_site,
                'user': user,
                'display_name': user.useraccount.display_name,
                'password_reset_url': url,
                'request': request,
            }
            if app_settings.AUTHENTICATION_METHOD != app_settings.AuthenticationMethod.EMAIL:
                context['username'] = user_username(user)
            get_adapter(request).send_mail('account/email/password_reset_key',
                                           email, context)
        return self.cleaned_data['email']

class CustomPasswordResetSerializer(PasswordResetSerializer):
    def get_email_options(self):
        return {
            'subject_template_name': 'account/email/password_reset_key_subject.txt',
            'email_template_name': 'account/email/password_reset_key_message.txt',
            'html_email_template_name': 'account/email/password_reset_key_message.html',
            'extra_email_context': {
                'pass_reset_obj': {}
            }
        }

    @property
    def password_reset_form_class(self):
        return CustomAllAuthPasswordResetForm
