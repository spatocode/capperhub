from django import forms

class UserAccountForm(forms.Form):
    first_name = forms.CharField(required=True)
    last_name = forms.CharField(required=True)
    username = forms.CharField(required=True)
    email = forms.EmailField(required=True)
    password = forms.CharField(required=True)
    mobile_no = forms.IntegerField(required=True)
    country = forms.CharField(required=True)
    is_predictor = forms.BooleanField(required=True)
