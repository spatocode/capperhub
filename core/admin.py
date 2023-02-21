from django.contrib import admin
from core.models.user import UserAccount, Pricing, Wallet
from core.models.transaction import Currency, Transaction
from core.models.play import Play
from core.models.bet import P2PBet, SportsEvent, P2PBetInvitation
from core.models.subscription import Subscription

class UserAccountAdmin(admin.ModelAdmin):
    list_display = ['username', 'email', 'first_name', 'last_name', 'display_name', 'country', 'phone_number', 'email_verified']
    list_filter = ['email_verified', 'country']

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

class TransactionAdmin(admin.ModelAdmin):
    list_display = ['type', 'amount', 'reference', 'issuer', 'channel', 'username', 'currency']

    def username(self, obj):
        return obj.user.username

    def currency(self, obj):
        return obj.currency

class SubscriptionAdmin(admin.ModelAdmin):
    list_display = ['type', 'issuer', 'subscriber', 'subscription_date', 'expiration_date', 'is_active']
    list_filter = ['type', 'is_active']

class PlayAdmin(admin.ModelAdmin):
    list_display = ['issuer', 'game', 'home_team', 'away_team', 'match_day', 'prediction', 'status']
    list_filter = ['issuer', 'game', 'match_day', 'status']

class PricingAdmin(admin.ModelAdmin):
    list_display = ['amount']
    list_filter = ['amount']

class WalletAdmin(admin.ModelAdmin):
    list_display = ['balance', 'bank', 'account_number']
    list_filter = ['bank']

class P2PBetAdmin(admin.ModelAdmin):
    list_display = ['issuer', 'player', 'market', 'issuer_option', 'player_option', 'winner', 'event', 'date_initialized', 'is_public', 'status']
    list_filter = ['date_initialized', 'is_public', 'status']

class P2PBetRequestAdmin(admin.ModelAdmin):
    list_display = ['bet', 'requestor', 'requestee', 'date_initialized']
    list_filter = ['date_initialized']

class SportsEventAdmin(admin.ModelAdmin):
    list_display = ['game', 'league', 'home', 'away', 'match_day', 'result']
    list_filter = ['game', 'league', 'match_day']

admin.site.register(UserAccount, UserAccountAdmin)
admin.site.register(Play, PlayAdmin)
admin.site.register(P2PBet, P2PBetAdmin)
admin.site.register(P2PBetInvitation, P2PBetRequestAdmin)
admin.site.register(SportsEvent, SportsEventAdmin)
admin.site.register(Pricing, PricingAdmin)
admin.site.register(Wallet, WalletAdmin)
admin.site.register(Subscription, SubscriptionAdmin)
admin.site.register(Currency, CurrencyAdmin)
admin.site.register(Transaction, TransactionAdmin)
