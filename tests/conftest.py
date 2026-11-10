"""Test fixtures: the real FastAPI app with a fake mailer that records messages."""

import pytest
from fastapi.testclient import TestClient

from src.backend.app import create_app
from src.backend.config import Settings
from src.backend.mailer import MailError


SETTINGS = Settings(contact_recipient="jeanette@example.com", contact_sender="website@example.com")


class FakeMailer:
    def __init__(self):
        self.sent = []
        self.fail = False

    def send(self, message):
        if self.fail:
            raise MailError("simulated failure")
        self.sent.append(message)


@pytest.fixture
def mailer():
    return FakeMailer()


@pytest.fixture
def client(mailer):
    with TestClient(create_app(SETTINGS, mailer=mailer)) as client:
        yield client
