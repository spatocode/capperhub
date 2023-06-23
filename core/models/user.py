import pytz
from datetime import datetime, timedelta
from django.conf import settings
from django.contrib.auth.models import User
from django.contrib.postgres.fields import ArrayField
from django.db import models
# from django.db.models.signals import post_save
# from django.dispatch import receiver
from django_countries.fields import CountryField
from hashlib import md5
from .subscription import Subscription
from core.shared.model_utils import optimize_image


def default_free_features():
    return ["Free plays forever"]

def default_premium_features():
    return ["Carefully picked plays"]


def meta_default():
    return {}


class Wallet(models.Model):
    currency = models.ForeignKey('core.Currency', on_delete=models.PROTECT)
    balance = models.FloatField(default=0.00)
    withheld = models.FloatField(default=0.00)
    bank_code = models.CharField(max_length=10, default="", blank=True)
    bank_account_number = models.CharField(max_length=50, default="", blank=True)
    authorizations = ArrayField(models.JSONField(), size=5, default=list, blank=True)
    meta = models.JSONField(default=meta_default)
    receipent_code = models.CharField(max_length=50, default="", blank=True)

    def __str__(self) -> str:
        return f'{self.balance} - {self.bank_code}'


class Pricing(models.Model):
    amount = models.DecimalField(default=0.00, max_digits=15, decimal_places=2)
    percentage_discount = models.DecimalField(default=0.0, max_digits=19, decimal_places=10)
    last_update = models.DateTimeField(auto_now=True)
    created_at = models.DateTimeField(auto_now_add=True)
    free_features = ArrayField(models.CharField(max_length=50), default=default_free_features, size=7)
    premium_features = ArrayField(models.CharField(max_length=50), default=default_premium_features, size=7)
    # play_frequency = models.CharField()

    def __str__(self):
        return f'{self.amount}'


class UserAccount(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    display_name = models.CharField(default="", max_length=50)
    bio = models.TextField(default="")
    image = models.FileField(null=True, blank=True)
    country = CountryField(default="", blank=True, blank_label="(Select country)")
    phone_number = models.CharField(null=True, unique=True, max_length=22)
    twitter_handle = models.CharField(default="", max_length=22, blank=True)
    facebook_handle = models.CharField(default="", max_length=22, blank=True)
    instagram_handle = models.CharField(default="", max_length=22, blank=True)
    pricing = models.ForeignKey('core.Pricing', on_delete=models.PROTECT)
    wallet = models.ForeignKey(Wallet, on_delete=models.PROTECT, related_name='wallet_owner')
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    last_updated = models.DateTimeField(auto_now=True, editable=False)

    def __str__(self):
        return f'{self.user.username}'

    @property
    def full_name(self):
        if not self.user.first_name or not self.user.last_name:
            return ""
        return f'{self.user.first_name} {self.user.last_name}'

    @property
    def is_punter(self):
        try:
            latest_play = self.playslip_set.latest('date_added')
            if latest_play.date_added + timedelta(days=14) > datetime.utcnow().replace(tzinfo=pytz.UTC):
                return True
            return False
        except:
            return False

    @property
    def subscription_issuers(self):
        subscribers = Subscription.objects.filter(
            subscriber=self.pk,
            is_active=True,
            type=Subscription.FREE
        ).values_list("issuer__user__username", flat=True)
        return subscribers

    @property
    def free_subscribers(self):
        subscribers = Subscription.objects.filter(
            issuer=self.pk,
            is_active=True,
            type=Subscription.FREE
        ).values_list("subscriber__user__username", flat=True)
        return subscribers
    
    @property
    def premium_subscribers(self):
        subscribers = Subscription.objects.filter(
            issuer=self.pk,
            is_active=True,
            type=Subscription.PREMIUM
        ).values_list("subscriber__user__username", flat=True)
        return subscribers

    def is_subscriber(self, issuer):
        subscriber_count = Subscription.objects.filter(
            issuer=issuer,
            subscriber=self.pk,
            is_active=True,
        ).count()

        if len(subscriber_count) > 0:
            return True
        return False
    
    def is_premium_subscriber(self, issuer):
        subscriber_count = Subscription.objects.filter(
            issuer=issuer,
            subscriber=self.pk,
            type=Subscription.PREMIUM,
            is_active=True,
        ).count()

        if len(subscriber_count) > 0:
            return True
        return False

    def save_avatar(self):
        digest = md5(self.user.email.encode('utf-8')).hexdigest()
        url = 'https://gravatar.com/avatar/{}?d=identicon'.format(digest)
        self.image.name = url

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        gravatar_uri = "https://gravatar.com/avatar/"
        if not settings.DEBUG and self.image.name and gravatar_uri not in self.image.name:
            self.image = optimize_image(self)
        elif not self.image:
            self.save_avatar()
        super(UserAccount, self).save()

    # @receiver(post_save, sender=User)
    # def create_user_profile(sender, instance, created, **kwargs):
    #     if created and not kwargs.get("raw", False):
    #         UserAccount.objects.create(user=instance)

    # @receiver(post_save, sender=User)
    # def save_user_profile(sender, instance, **kwargs):
    #     instance.useraccount.save()
