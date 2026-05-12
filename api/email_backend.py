import os
import ssl

from django.core.mail.backends.smtp import EmailBackend as DjangoSMTPEmailBackend


class EmailBackend(DjangoSMTPEmailBackend):
    @property
    def ssl_context(self):
        context = super().ssl_context
        disable_verify = os.getenv('EMAIL_DISABLE_CERT_VERIFY', 'False') == 'True'
        if disable_verify:
            context.check_hostname = False
            context.verify_mode = ssl.CERT_NONE
        return context
