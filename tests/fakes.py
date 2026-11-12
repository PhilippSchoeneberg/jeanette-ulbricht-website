"""Test doubles shared by the API tests and the browser tests."""

from src.backend.mailer import MailError


class FakeMailer:
    """Records messages instead of sending them; set `fail` to simulate a mail server error."""

    def __init__(self):
        self.sent = []
        self.fail = False

    def send(self, message):
        if self.fail:
            raise MailError("simulated failure")
        # Serialize like a real SMTP send, so messages that can't be encoded fail here too.
        message.as_bytes()
        self.sent.append(message)
