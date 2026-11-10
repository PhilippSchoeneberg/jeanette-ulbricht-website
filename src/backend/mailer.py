"""Sending e-mails: via SMTP in production, to the console in development."""

import logging
import smtplib
import ssl
from email.message import EmailMessage

from .config import SmtpSettings


logger = logging.getLogger(__name__)

SMTP_TIMEOUT_SECONDS = 15


class MailError(Exception):
    """The message could not be handed to the mail server."""


class SmtpMailer:
    def __init__(self, settings: SmtpSettings):
        self.settings = settings

    def send(self, message: EmailMessage) -> None:
        s = self.settings
        context = ssl.create_default_context()
        try:
            if s.security == "ssl":
                server = smtplib.SMTP_SSL(s.host, s.port, timeout=SMTP_TIMEOUT_SECONDS, context=context)
            else:
                server = smtplib.SMTP(s.host, s.port, timeout=SMTP_TIMEOUT_SECONDS)
            with server:
                if s.security == "starttls":
                    server.starttls(context=context)
                if s.username:
                    server.login(s.username, s.password)
                server.send_message(message)
        except (smtplib.SMTPException, OSError) as exc:
            logger.error("Sending contact message failed: %s", exc)
            raise MailError from exc


class ConsoleMailer:
    """Development stand-in: prints the message instead of sending it."""

    def send(self, message: EmailMessage) -> None:
        headers = "\n".join(f"{name}: {message[name]}" for name in ("From", "To", "Reply-To", "Subject"))
        logger.warning("SMTP_HOST is not set, contact message NOT sent:\n%s\n\n%s", headers, message.get_content())
