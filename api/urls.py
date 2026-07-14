from django.urls import path

from .views import (
    LoginView, 
    ResendOTPView, 
    SignupView, 
    VerifyOTPView,
    SendTransferView,
    TransferDetailView,
    RedeemTransferView,
    UserProfileView,
    TransferHistoryView,
    TopUpView,
)

urlpatterns = [
    path('signup/', SignupView.as_view(), name='signup'),
    path('login/', LoginView.as_view(), name='login'),
    path('verify-otp/', VerifyOTPView.as_view(), name='verify-otp'),
    path('resend-otp/', ResendOTPView.as_view(), name='resend-otp'),
    path('users/profile/', UserProfileView.as_view(), name='user-profile'),
    path('users/topup/', TopUpView.as_view(), name='user-topup'),
    path('transfers/', TransferHistoryView.as_view(), name='transfer-history'),
    path('transfers/send/', SendTransferView.as_view(), name='send-transfer'),
    path('transfers/<uuid:pk>/', TransferDetailView.as_view(), name='transfer-detail'),
    path('transfers/<uuid:pk>/redeem/', RedeemTransferView.as_view(), name='redeem-transfer'),
]

