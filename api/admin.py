from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from .models import EmailOTP, Transfer, User


@admin.register(User)
class CustomUserAdmin(UserAdmin):
    fieldsets = UserAdmin.fieldsets + (
        ('Additional Info', {'fields': ('phone',)}),
    )
    list_display = ('username', 'email', 'phone', 'is_active', 'is_staff', 'created_at')
    list_filter = ('is_active', 'is_staff', 'is_superuser')
    search_fields = ('username', 'email', 'phone')
    ordering = ('-created_at',)
    readonly_fields = ('created_at', 'updated_at', 'last_login', 'date_joined')


@admin.register(EmailOTP)
class EmailOTPAdmin(admin.ModelAdmin):
    list_display = ('user', 'code', 'is_used', 'created_at', 'expires_at')
    list_filter = ('is_used',)
    search_fields = ('user__username', 'user__email', 'code')
    readonly_fields = ('created_at',)


@admin.register(Transfer)
class TransferAdmin(admin.ModelAdmin):
    list_display = (
        'created_at',
        'sender',
        'recipient_email',
        'amount',
        'token',
        'subject',
        'message_preview',
        'status',
    )
    list_filter = ('status', 'token', 'created_at')
    search_fields = (
        'recipient_email',
        'subject',
        'message',
        'sender__username',
        'sender__email',
    )
    readonly_fields = ('id', 'created_at')
    autocomplete_fields = ('sender',)
    date_hierarchy = 'created_at'
    ordering = ('-created_at',)

    fieldsets = (
        (None, {'fields': ('id', 'sender', 'status', 'created_at')}),
        ('Recipient & payout', {'fields': ('recipient_email', 'amount', 'token')}),
        ('Email content', {'fields': ('subject', 'message')}),
    )

    @admin.display(description='Message')
    def message_preview(self, obj):
        if not obj.message:
            return '—'
        text = obj.message.strip()
        if len(text) > 50:
            return f'{text[:50]}…'
        return text
