from django.contrib import admin
from product_api.models import football, base


class CurrencyAdmin(admin.ModelAdmin):
    list_display = ['code']

admin.site.register(base.Currency, CurrencyAdmin)


class FootballTeamAdmin(admin.ModelAdmin):
    list_display = ['id', 'name']

admin.site.register(football.FootballTeam, FootballTeamAdmin)


class ProductAdmin(admin.ModelAdmin):
    list_display = ['id', 'type', 'owner', 'price']
    list_filter = ['type', 'owner__country']

admin.site.register(base.Product, ProductAdmin)


class FootballPredictionAdmin(admin.ModelAdmin):
    list_display = ['id', 'product', 'type', 'home_team', 'away_team', 'match_day', 'pick']
    list_filter = ['type', 'product__type', 'match_day']

admin.site.register(football.FootballPrediction, FootballPredictionAdmin)
