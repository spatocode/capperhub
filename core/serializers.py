from django.contrib.auth.models import User
from rest_framework import serializers
from dj_rest_auth.registration.serializers import RegisterSerializer
from core.models.user import UserAccount
from core.models.tips import Tips

class UserAccountRegisterSerializer(RegisterSerializer):
    username = serializers.CharField(required=False)
    first_name = serializers.CharField(required=True)
    last_name = serializers.CharField(required=True)
    email = serializers.EmailField(required=True)
    password1 = serializers.CharField(write_only=True, required=True)
    password2 = serializers.CharField(write_only=True, required=True)
    phone_number = serializers.CharField(required=False)
    is_tipster = serializers.BooleanField(required=False)

    def get_cleaned_data(self):
        super(UserAccountRegisterSerializer, self).get_cleaned_data()

        return {
            'username': self.validated_data.get('username', ''),
            'first_name': self.validated_data.get('first_name', ''),
            'last_name': self.validated_data.get('last_name', ''),
            'password1': self.validated_data.get('password1', ''),
            'password2': self.validated_data.get('password2', ''),
            'email': self.validated_data.get('email', ''),
            'cell_phone': self.validated_data.get('phone_number', ''),
            'is_tipster': self.validated_data.get('is_tipster', ''),
        }


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        exclude = ['password']


class UserAccountSerializer(serializers.ModelSerializer):
    user = UserSerializer()
    num_of_subscribers = serializers.IntegerField(required=False)

    class Meta:
        model = UserAccount
        exclude = ['ip_address']


class TipsSerializer(serializers.ModelSerializer):

    def validate_owner(self, value):
        """
        Check that the owner is a tipster
        """
        user_account = value
        if not user_account.is_tipster:
            raise serializers.ValidationError("Only Tipsters can create a tip")
        return value

    class Meta:
        model = Tips
        fields = '__all__'
        read_only_fields = ['id']
