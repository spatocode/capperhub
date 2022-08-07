from django.contrib import admin

from product_auth_api import models


class UserAccountAdmin(admin.ModelAdmin):
    list_display = ['id', 'user', 'country', 'mobile_no', 'is_predictor', 'email_verified']
    list_filter = ['country', 'is_predictor', 'email_verified']

admin.site.register(models.UserAccount, UserAccountAdmin)
