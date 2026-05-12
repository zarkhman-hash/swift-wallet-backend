import random
from datetime import timedelta

from django.conf import settings
from django.contrib.auth import authenticate, get_user_model
from django.core.mail import send_mail
from django.db import transaction
from django.utils import timezone
from rest_framework import status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken

from .models import EmailOTP, Transfer
from .serializers import ResendOTPSerializer, SignupSerializer, VerifyOTPSerializer, TransferSerializer

User = get_user_model()


def generate_otp_code():
    return f"{random.randint(0, 999999):06d}"


def is_email_service_configured():
    if settings.EMAIL_BACKEND == 'django.core.mail.backends.locmem.EmailBackend':
        return True

    smtp_backends = {
        'django.core.mail.backends.smtp.EmailBackend',
        'api.email_backend.EmailBackend',
    }
    if settings.EMAIL_BACKEND not in smtp_backends:
        return False

    return bool(
        settings.EMAIL_HOST
        and settings.EMAIL_PORT
        and settings.EMAIL_HOST_USER
        and settings.EMAIL_HOST_PASSWORD
    )


def send_otp_email(user, code):
    send_mail(
        subject='Your SwiftWallet verification code',
        message=(
            f'Hi {user.username},\n\n'
            f'Your SwiftWallet verification code is: {code}\n'
            f'This code expires in {settings.OTP_EXPIRY_MINUTES} minutes.\n\n'
            'If you did not request this code, please ignore this email.'
        ),
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[user.email],
        fail_silently=False,
    )


class SignupView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        if not is_email_service_configured():
            return Response(
                {
                    'detail': (
                        'Email service is not configured. '
                        'Set EMAIL_HOST_USER and EMAIL_HOST_PASSWORD in backend .env.'
                    )
                },
                status=status.HTTP_503_SERVICE_UNAVAILABLE,
            )

        serializer = SignupSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        code = generate_otp_code()

        with transaction.atomic():
            user = serializer.save()
            EmailOTP.objects.filter(user=user, is_used=False).update(is_used=True)
            EmailOTP.objects.create(
                user=user,
                code=code,
                expires_at=timezone.now()
                + timedelta(minutes=settings.OTP_EXPIRY_MINUTES),
            )
            try:
                send_otp_email(user, code)
            except Exception:
                transaction.set_rollback(True)
                return Response(
                    {
                        'detail': (
                            'We could not send OTP email right now. '
                            'Please verify SMTP credentials and try again.'
                        )
                    },
                    status=status.HTTP_502_BAD_GATEWAY,
                )

        return Response(
            {
                'message': 'Account created. Please verify OTP sent to your email.',
                'username': user.username,
                'email': user.email,
            },
            status=status.HTTP_201_CREATED,
        )


class LoginView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        username = request.data.get('username')
        password = request.data.get('password')

        if not username or not password:
            return Response(
                {'detail': 'Username and password are required.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        existing_user = User.objects.filter(username=username).first()
        if existing_user and not existing_user.is_active and existing_user.check_password(
            password
        ):
            return Response(
                {'detail': 'Please verify your account using OTP before logging in.'},
                status=status.HTTP_403_FORBIDDEN,
            )

        user = authenticate(username=username, password=password)
        if user is None:
            return Response(
                {'detail': 'Invalid credentials.'},
                status=status.HTTP_401_UNAUTHORIZED,
            )

        refresh = RefreshToken.for_user(user)
        return Response(
            {
                'access': str(refresh.access_token),
                'refresh': str(refresh),
                'username': user.username,
            },
            status=status.HTTP_200_OK,
        )


class VerifyOTPView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = VerifyOTPSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        email = serializer.validated_data['email']
        code = serializer.validated_data['code']
        user = User.objects.filter(email__iexact=email).first()

        if user is None:
            return Response(
                {'detail': 'No account found with this email.'},
                status=status.HTTP_404_NOT_FOUND,
            )

        if user.is_active:
            return Response(
                {'detail': 'Account is already verified.'},
                status=status.HTTP_200_OK,
            )

        otp = user.email_otps.filter(is_used=False).first()
        if otp is None:
            return Response(
                {'detail': 'OTP not found. Please request a new code.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if otp.expires_at < timezone.now():
            otp.is_used = True
            otp.save(update_fields=['is_used'])
            return Response(
                {'detail': 'OTP has expired. Please request a new code.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if otp.code != code:
            return Response(
                {'detail': 'Invalid OTP code.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        otp.is_used = True
        otp.save(update_fields=['is_used'])
        user.is_active = True
        user.save(update_fields=['is_active'])

        return Response(
            {'message': 'Account verified successfully. You can login now.'},
            status=status.HTTP_200_OK,
        )


class ResendOTPView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        if not is_email_service_configured():
            return Response(
                {
                    'detail': (
                        'Email service is not configured. '
                        'Set EMAIL_HOST_USER and EMAIL_HOST_PASSWORD in backend .env.'
                    )
                },
                status=status.HTTP_503_SERVICE_UNAVAILABLE,
            )

        serializer = ResendOTPSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        email = serializer.validated_data['email']
        user = User.objects.filter(email__iexact=email).first()

        if user is None:
            return Response(
                {'detail': 'No account found with this email.'},
                status=status.HTTP_404_NOT_FOUND,
            )

        if user.is_active:
            return Response(
                {'detail': 'Account is already verified. Please login.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        code = generate_otp_code()
        with transaction.atomic():
            EmailOTP.objects.filter(user=user, is_used=False).update(is_used=True)
            EmailOTP.objects.create(
                user=user,
                code=code,
                expires_at=timezone.now()
                + timedelta(minutes=settings.OTP_EXPIRY_MINUTES),
            )
            try:
                send_otp_email(user, code)
            except Exception:
                transaction.set_rollback(True)
                return Response(
                    {'detail': 'Unable to resend OTP right now. Please try again.'},
                    status=status.HTTP_502_BAD_GATEWAY,
                )

        return Response(
            {'message': 'A new OTP has been sent to your email.'},
            status=status.HTTP_200_OK,
        )


class SendTransferView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = TransferSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        email_errors: list[str] = []

        with transaction.atomic():
            transfer = serializer.save(sender=request.user)
            transfer_id = transfer.pk
            sender_username = request.user.username

            def send_notification_after_commit():
                try:
                    t = Transfer.objects.get(pk=transfer_id)
                except Transfer.DoesNotExist:
                    return
                try:
                    frontend_url = getattr(settings, 'FRONTEND_URL', 'http://localhost:5173')
                    redeem_link = f"{frontend_url}/redeem/{t.id}"
                    body = (
                        f"You have received {t.amount} {t.token} from {sender_username}.\n\n"
                    )
                    if t.message:
                        body += f"Message: {t.message}\n\n"
                    body += f"Click here for redeem:\n{redeem_link}"

                    send_mail(
                        subject=t.subject,
                        message=body,
                        from_email=settings.DEFAULT_FROM_EMAIL,
                        recipient_list=[t.recipient_email],
                        fail_silently=False,
                    )
                except Exception as e:
                    print(f"Exception during email send: {e}")
                    email_errors.append(str(e))

            transaction.on_commit(send_notification_after_commit)

        payload = dict(TransferSerializer(transfer).data)
        if email_errors:
            payload['email_sent'] = False
            payload['detail'] = (
                f'Unable to send email right now. Error: {email_errors[0]}. '
                'Transfer is saved; you can share the redeem link manually.'
            )
            return Response(payload, status=status.HTTP_201_CREATED)

        payload['email_sent'] = True
        return Response(payload, status=status.HTTP_201_CREATED)


class TransferDetailView(APIView):
    permission_classes = [AllowAny]

    def get(self, request, pk):
        try:
            transfer = Transfer.objects.get(pk=pk)
        except Transfer.DoesNotExist:
            return Response({'detail': 'Transfer not found.'}, status=status.HTTP_404_NOT_FOUND)
            
        serializer = TransferSerializer(transfer)
        return Response(serializer.data, status=status.HTTP_200_OK)


class RedeemTransferView(APIView):
    permission_classes = [AllowAny]

    def post(self, request, pk):
        try:
            transfer = Transfer.objects.get(pk=pk)
        except Transfer.DoesNotExist:
            return Response({'detail': 'Transfer not found.'}, status=status.HTTP_404_NOT_FOUND)
            
        if transfer.status == 'redeemed':
            return Response({'detail': 'Transfer has already been redeemed.'}, status=status.HTTP_400_BAD_REQUEST)
            
        transfer.status = 'redeemed'
        transfer.save(update_fields=['status'])
        
        serializer = TransferSerializer(transfer)
        return Response(serializer.data, status=status.HTTP_200_OK)
