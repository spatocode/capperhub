from django.contrib import admin
from core.models.user import UserAccount, Pricing, Wallet
from core.models.transaction import Currency, Transaction
from core.models.play import Play
from core.models.wager import SportsWager, SportsWagerChallenge
from core.models.games import SportsGame, Sport
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
    list_display = ['type', 'amount', 'balance', 'reference', 'payment_issuer', 'channel', 'user', 'currency', 'status']
    list_filter = ['type', 'status']

    def user(self, obj):
        return obj.user.username

    def currency(self, obj):
        return obj.currency

class SubscriptionAdmin(admin.ModelAdmin):
    list_display = ['type', 'issuer', 'subscriber', 'subscription_date', 'expiration_date', 'is_active']
    list_filter = ['type', 'is_active']

class PlayAdmin(admin.ModelAdmin):
    list_display = ['issuer', 'sports', 'home_team', 'away_team', 'match_day', 'prediction', 'status']
    list_filter = ['issuer', 'sports', 'match_day', 'status']

class PricingAdmin(admin.ModelAdmin):
    list_display = ['amount']
    list_filter = ['amount']

class WalletAdmin(admin.ModelAdmin):
    list_display = ['balance', 'withheld', 'bank_name', 'bank_account_number']
    list_filter = ['bank_name']

class SportsWagerAdmin(admin.ModelAdmin):
    list_display = ['backer', 'layer', 'market', 'backer_option', 'layer_option', 'winner', 'game', 'placed_time', 'is_public', 'status']
    list_filter = ['matched', 'matched_time', 'is_public', 'status']

class SportsWagerChallengeAdmin(admin.ModelAdmin):
    list_display = ['wager', 'requestor', 'requestee', 'date_initialized', 'accepted']
    list_filter = ['date_initialized', 'accepted']

class SportsGameAdmin(admin.ModelAdmin):
    list_display = ['type', 'competition', 'home', 'away', 'match_day', 'result']
    list_filter = ['type', 'competition', 'match_day']

class SportsAdmin(admin.ModelAdmin):
    list_display = ['name']

admin.site.register(UserAccount, UserAccountAdmin)
admin.site.register(Play, PlayAdmin)
admin.site.register(SportsWager, SportsWagerAdmin)
admin.site.register(SportsWagerChallenge, SportsWagerChallengeAdmin)
admin.site.register(SportsGame, SportsGameAdmin)
admin.site.register(Sport, SportsAdmin)
admin.site.register(Pricing, PricingAdmin)
admin.site.register(Wallet, WalletAdmin)
admin.site.register(Subscription, SubscriptionAdmin)
admin.site.register(Currency, CurrencyAdmin)
admin.site.register(Transaction, TransactionAdmin)
