from django.core.mail.backends.smtp import EmailBackend
from django.core.mail.message import sanitize_address
from django.utils.encoding import force_bytes
from django.conf import settings


class RedirectEmailBackend(EmailBackend):
    """ Redirects all outgoing mails to a sepcified email address.
        Useful for staging purposes.

        Settings:
            EMAIL_BACKEND = 'masala.mail.backends.RedirectEmailBackend'
            REDIRECT_ALL_EMAIL_TO = 'somemailbox+{identifier}@somedomain.com'
    """
    def _send(self, email_message):
        """A helper method that does the actual sending."""
        if not email_message.recipients():
            return False
        to = [self._process_addr(addr, email_message.encoding) for addr in email_message.to]
        cc = [self._process_addr(addr, email_message.encoding) for addr in email_message.cc]
        bcc = [self._process_addr(addr, email_message.encoding) for addr in email_message.bcc]

        email_message.to = to
        email_message.cc = cc
        email_message.bcc = bcc
        email_message.subject = '[STAGING]: ' + email_message.subject
        return super(RedirectEmailBackend, self)._send(email_message)

    def _process_addr(self, addr, encoding):
        addr = sanitize_address(addr, encoding)
        addr = addr.replace('@', '_at_')
        addr = addr.replace('.', '_')
        return settings.REDIRECT_ALL_EMAIL_TO.format(identifier=addr)

