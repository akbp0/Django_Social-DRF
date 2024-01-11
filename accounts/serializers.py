from dj_rest_auth.registration.serializers import RegisterSerializer
from django.contrib.auth import get_user_model
from rest_framework import serializers
from dj_rest_auth.serializers import (
    LoginSerializer, PasswordResetSerializer, PasswordResetConfirmSerializer, PasswordChangeSerializer
)
User = get_user_model()


class CustomLoginSerializer(LoginSerializer):
    username = None


class CustomRegisterSerializer(RegisterSerializer):

    first_name = serializers.CharField(
        max_length=150, required=False, allow_blank=True, allow_null=True)
    last_name = serializers.CharField(
        max_length=150, required=False, allow_blank=True, allow_null=True)

    def get_cleaned_data(self):
        return {
            'first_name': self.validated_data.get('first_name', ''),
            'last_name': self.validated_data.get('last_name', ''),
            'password1': self.validated_data.get('password1', ''),
            'email': self.validated_data.get('email', ''),
        }
