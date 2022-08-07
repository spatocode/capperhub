from django.contrib.auth.models import User
from product_auth_api.models import UserAccount
from rest_framework import serializers


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        exclude = ['password']


class UserAccountSerializer(serializers.ModelSerializer):
    user = UserSerializer()
    class Meta:
        model = UserAccount
        fields = '__all__'
