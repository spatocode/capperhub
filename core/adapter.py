from django.conf import settings
from django.contrib.sites.shortcuts import get_current_site
from allauth.account.adapter import DefaultAccountAdapter
from core.models.user import UserAccount

class CustomDefaultAccountAdapter(DefaultAccountAdapter):
    def send_confirmation_mail(self, request, emailconfirmation, signup):
        current_site = get_current_site(request)
        # activate_url = self.get_email_confirmation_url(request, emailconfirmation)
        ctx = {
            "user": emailconfirmation.email_address.user,
            "activate_url": settings.CLIENT_ACTIVATE_ACCOUNT_URL + '/' + emailconfirmation.key,
            "current_site": current_site,
            "key": emailconfirmation.key,
        }
        if signup:
            email_template = "account/email/email_confirmation_signup"
        else:
            email_template = "account/email/email_confirmation"
        self.send_mail(email_template, emailconfirmation.email_address.email, ctx)
