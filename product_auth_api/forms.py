from django import forms
from django.contrib.auth.hashers import make_password

class UserAccountForm(forms.Form):
    first_name = forms.CharField(required=True)
    last_name = forms.CharField(required=True)
    username = forms.CharField(required=True)
    email = forms.EmailField(required=True)
    password = forms.CharField(required=True)
    mobile_no = forms.IntegerField(required=True)
    country = forms.CharField(required=True)
    is_predictor = forms.BooleanField(required=False)

    def _post_clean(self):
        # Data massage only if form is valid
        if self.is_valid():
            password = self.cleaned_data.pop('password')
            self.cleaned_data.update({
                'password': make_password(password),
            })
