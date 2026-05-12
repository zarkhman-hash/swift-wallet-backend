from django.contrib.auth import get_user_model
from rest_framework import serializers

from .models import Transfer

User = get_user_model()


class SignupSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, min_length=6)
    email = serializers.EmailField()

    class Meta:
        model = User
        fields = ('username', 'email', 'password')

    def validate_email(self, value):
        if User.objects.filter(email__iexact=value).exists():
            raise serializers.ValidationError('A user with this email already exists.')
        return value

    def validate_username(self, value):
        if User.objects.filter(username__iexact=value).exists():
            raise serializers.ValidationError('A user with this username already exists.')
        return value

    def create(self, validated_data):
        return User.objects.create_user(
            username=validated_data['username'],
            email=validated_data['email'],
            password=validated_data['password'],
            is_active=False,
        )


class VerifyOTPSerializer(serializers.Serializer):
    email = serializers.EmailField()
    code = serializers.RegexField(
        regex=r'^\d{6}$',
        error_messages={'invalid': 'OTP must be 6 digits.'},
    )


class ResendOTPSerializer(serializers.Serializer):
    email = serializers.EmailField()


class TransferSerializer(serializers.ModelSerializer):
    sender_name = serializers.CharField(source='sender.username', read_only=True)
    sender_email = serializers.CharField(source='sender.email', read_only=True)

    class Meta:
        model = Transfer
        fields = [
            'id',
            'sender',
            'sender_name',
            'sender_email',
            'recipient_email',
            'subject',
            'token',
            'amount',
            'message',
            'status',
            'created_at',
        ]
        read_only_fields = ['id', 'sender', 'status', 'created_at']
