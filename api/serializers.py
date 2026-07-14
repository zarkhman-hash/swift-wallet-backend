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
            'sender_wallet_address',
            'recipient_email',
            'recipient_wallet_address',
            'subject',
            'token',
            'amount',
            'message',
            'status',
            'privacy_mode',
            'escrow_status',
            'escrow_tx_hash',
            'escrow_release_tx_hash',
            'created_at',
        ]
        read_only_fields = [
            'id',
            'sender',
            'sender_wallet_address',
            'recipient_wallet_address',
            'status',
            'escrow_status',
            'escrow_tx_hash',
            'escrow_release_tx_hash',
            'created_at',
        ]

    def to_representation(self, instance):
        data = super().to_representation(instance)
        request = self.context.get('request')
        is_sender = (
            request is not None
            and getattr(request, 'user', None) is not None
            and request.user.is_authenticated
            and request.user.pk == instance.sender_id
        )
        # Privacy shield: recipients / public redeemers only see amount + token
        if instance.privacy_mode and not is_sender:
            data['sender'] = None
            data['sender_name'] = 'Anonymous'
            data['sender_email'] = ''
            data['sender_wallet_address'] = ''
        return data


class UserProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['username', 'email', 'wallet_address', 'balance']
