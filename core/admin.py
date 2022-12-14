from django.contrib import admin
from core.models.user import UserAccount, Currency
from core.models.currency import Currency
from core.models.tips import Tips

class UserAccountAdmin(admin.ModelAdmin):
    list_display = ['username', 'email', 'first_name', 'last_name', 'country', 'phone_number', 'is_tipster', 'email_verified']
    list_filter = ['country', 'is_tipster', 'email_verified']

    def username(self, obj):
        return obj.user.username
    
    def email(self, obj):
        return obj.user.email

    def first_name(self, obj):
        return obj.user.first_name

    def last_name(self, obj):
        return obj.user.last_name


class CurrencyAdmin(admin.ModelAdmin):
    list_display = ['code']

class TipsAdmin(admin.ModelAdmin):
    list_display = ['issuer', 'sport', 'home_team', 'away_team', 'date', 'prediction', 'success', 'published']
    list_filter = ['issuer', 'sport', 'date', 'published', 'success']


admin.site.register(UserAccount, UserAccountAdmin)
admin.site.register(Tips, TipsAdmin)
admin.site.register(Currency, CurrencyAdmin)
