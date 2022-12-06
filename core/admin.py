from django.contrib import admin
from core.models.user import UserAccount, Currency
from core.models.tips import SportsTips

class UserAccountAdmin(admin.ModelAdmin):
    list_display = ['username', 'id', 'email', 'first_name', 'last_name', 'country', 'phone_number', 'price', 'is_tipster', 'email_verified']
    list_filter = ['price', 'country', 'is_tipster', 'email_verified']

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

class SportsTipsAdmin(admin.ModelAdmin):
    list_display = ['owner', 'id', 'sport', 'home_team', 'away_team', 'date', 'prediction']
    list_filter = ['owner', 'sport', 'date', 'success']


admin.site.register(UserAccount, UserAccountAdmin)
admin.site.register(SportsTips, SportsTipsAdmin)
admin.site.register(Currency, CurrencyAdmin)
