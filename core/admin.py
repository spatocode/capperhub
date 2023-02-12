from django.contrib import admin
from core.models.user import UserAccount, Pricing, Wallet
from core.models.currency import Currency
from core.models.tips import MatchTips
from core.models.subscription import Subscription

class UserAccountAdmin(admin.ModelAdmin):
    list_display = ['username', 'email', 'first_name', 'last_name', 'display_name', 'country', 'phone_number', 'is_tipster', 'email_verified']
    list_filter = ['is_tipster', 'email_verified', 'country']

    def username(self, obj):
        return obj.user.username
    
    def email(self, obj):
        return obj.user.email

    def first_name(self, obj):
        return obj.user.first_name

    def last_name(self, obj):
        return obj.user.last_name

class CurrencyAdmin(admin.ModelAdmin):
    list_display = ['code', 'country']

class SubscriptionAdmin(admin.ModelAdmin):
    list_display = ['type', 'issuer', 'subscriber', 'subscription_date', 'expiration_date', 'is_active']
    list_filter = ['type', 'is_active']

class MatchTipsAdmin(admin.ModelAdmin):
    list_display = ['issuer', 'game', 'home_team', 'away_team', 'match_day', 'prediction', 'status']
    list_filter = ['issuer', 'game', 'match_day', 'status']

class BookingCodeTipsAdmin(admin.ModelAdmin):
    list_display = ['code', 'bookie', 'issuer', 'date_added', 'is_free']
    list_filter = ['bookie', 'date_added', 'is_free']

class PricingAdmin(admin.ModelAdmin):
    list_display = ['amount']
    list_filter = ['amount']

class WalletAdmin(admin.ModelAdmin):
    list_display = ['balance', 'bank', 'account_number']
    list_filter = ['bank']

    # def username(self, obj):
    #     import pdb; pdb.set_trace()
    #     return obj.useraccount_set.object.user.username


admin.site.register(UserAccount, UserAccountAdmin)
admin.site.register(MatchTips, MatchTipsAdmin)
admin.site.register(Pricing, PricingAdmin)
admin.site.register(Wallet, WalletAdmin)
admin.site.register(Subscription, SubscriptionAdmin)
admin.site.register(Currency, CurrencyAdmin)
