import pytest

from src.backend.app import create_app
from src.backend.config import Settings
from src.backend.rate_limit import RateLimiter


VALID = {
    "name": "Erika Mustermann",
    "email": "erika@example.org",
    "subject": "Anfrage Flyer",
    "message": "Hallo, ich hätte gern ein Angebot für einen Flyer.",
}


def test_valid_message_is_sent(client, mailer):
    response = client.post("/api/contact", json=VALID)

    assert response.status_code == 200
    assert response.json() == {"status": "sent"}
    assert len(mailer.sent) == 1
    message = mailer.sent[0]
    assert message["To"] == "jeanette@example.com"
    assert "website@example.com" in message["From"]
    assert message["Reply-To"] == "Erika Mustermann <erika@example.org>"
    assert message["Subject"] == "Kontaktformular: Anfrage Flyer"
    body = message.get_content()
    assert "Erika Mustermann" in body
    assert "ein Angebot für einen Flyer" in body


def test_subject_is_optional(client, mailer):
    data = {k: v for k, v in VALID.items() if k != "subject"}

    response = client.post("/api/contact", json=data)

    assert response.status_code == 200
    assert mailer.sent[0]["Subject"] == "Kontaktformular: Neue Nachricht"


def test_whitespace_is_trimmed(client, mailer):
    client.post("/api/contact", json={**VALID, "name": "  Erika  "})

    assert mailer.sent[0]["Reply-To"] == "Erika <erika@example.org>"


@pytest.mark.parametrize("field, value", [
    ("name", ""),
    ("name", "x" * 101),
    ("email", "not-an-address"),
    ("message", "zu kurz"),
    ("message", "x" * 5001),
    ("subject", "x" * 151),
])
def test_invalid_fields_are_rejected(client, mailer, field, value):
    response = client.post("/api/contact", json={**VALID, field: value})

    assert response.status_code == 422
    assert response.json()["detail"][0]["loc"][-1] == field
    assert mailer.sent == []


@pytest.mark.parametrize("field", ["name", "subject"])
def test_header_injection_is_rejected(client, mailer, field):
    response = client.post("/api/contact", json={**VALID, field: "Hallo\r\nBcc: victim@example.com"})

    assert response.status_code == 422
    assert mailer.sent == []


def test_unknown_fields_are_rejected(client, mailer):
    response = client.post("/api/contact", json={**VALID, "bcc": "victim@example.com"})

    assert response.status_code == 422
    assert mailer.sent == []


def test_honeypot_pretends_success_but_sends_nothing(client, mailer):
    response = client.post("/api/contact", json={**VALID, "website": "https://spam.example"})

    assert response.status_code == 200
    assert mailer.sent == []


def test_mail_failure_returns_502(client, mailer):
    mailer.fail = True

    response = client.post("/api/contact", json=VALID)

    assert response.status_code == 502
    assert response.json() == {"detail": "mail_error"}


def test_rate_limit(mailer):
    from fastapi.testclient import TestClient

    settings = Settings(contact_recipient="j@example.com", contact_sender="w@example.com", rate_limit_count=2)
    with TestClient(create_app(settings, mailer=mailer)) as client:
        assert client.post("/api/contact", json=VALID).status_code == 200
        assert client.post("/api/contact", json=VALID).status_code == 200
        response = client.post("/api/contact", json=VALID)

    assert response.status_code == 429
    assert response.json() == {"detail": "rate_limited"}
    assert len(mailer.sent) == 2


def test_rate_limiter_window_expires():
    now = [1000.0]
    limiter = RateLimiter(max_requests=1, window_seconds=60, clock=lambda: now[0])

    assert limiter.allow("1.2.3.4")
    assert not limiter.allow("1.2.3.4")
    assert limiter.allow("5.6.7.8")
    now[0] += 61
    assert limiter.allow("1.2.3.4")


def test_frontend_is_served(client):
    response = client.get("/")

    assert response.status_code == 200
    assert "Jeanette Ulbricht" in response.text
    assert client.get("/contact.html").status_code == 200
