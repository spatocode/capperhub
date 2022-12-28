from django.contrib import admin
from core.models.user import UserAccount, Pricing
from core.models.currency import Currency
from core.models.tips import Tips, Game
from core.models.subscription import Subscription

class UserAccountAdmin(admin.ModelAdmin):
    list_display = ['username', 'email', 'first_name', 'last_name', 'country', 'phone_number', 'is_tipster', 'email_verified']
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
    list_display = ['type', 'issuer', 'subscriber', 'date_initialized', 'date_expired', 'is_active']
    list_filter = ['type', 'is_active']

class TipsAdmin(admin.ModelAdmin):
    list_display = ['issuer', 'game', 'home_team', 'away_team', 'date', 'prediction', 'status']
    list_filter = ['issuer', 'game', 'date', 'status']

class GameAdmin(admin.ModelAdmin):
    list_display = ['id', 'type']
    list_filter = ['type']


class PricingAdmin(admin.ModelAdmin):
    list_display = ['amount']
    list_filter = ['amount']


admin.site.register(UserAccount, UserAccountAdmin)
admin.site.register(Tips, TipsAdmin)
admin.site.register(Game, GameAdmin)
admin.site.register(Pricing, PricingAdmin)
admin.site.register(Subscription, SubscriptionAdmin)
admin.site.register(Currency, CurrencyAdmin)
