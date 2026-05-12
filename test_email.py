import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from django.core.mail import send_mail
from django.conf import settings

print("EMAIL_HOST:", settings.EMAIL_HOST)
print("EMAIL_HOST_USER:", settings.EMAIL_HOST_USER)
print("EMAIL_PORT:", settings.EMAIL_PORT)

try:
    send_mail(
        subject="Test Email",
        message="This is a test.",
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=["zarkhman122@gmail.com"],
        fail_silently=False,
    )
    print("Email sent successfully!")
except Exception as e:
    print(f"Error: {e}")
