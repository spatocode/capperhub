from django.db import models

class TermsOfUse(models.Model):
    text = models.TextField(max_length=100000)
    last_update = models.DateTimeField(auto_now=True)


class PrivacyPolicy(models.Model):
    text = models.TextField(max_length=100000)
    last_update = models.DateTimeField(auto_now=True)


class Feedback(models.Model):
    email = models.EmailField()
    message = models.TextField(max_length=10000)
    date_added = models.DateTimeField(auto_now_add=True)


class Waitlist(models.Model):
    email = models.EmailField()
    date_added = models.DateTimeField(auto_now_add=True)
