"""Security hardening: response headers, request size limit, API docs switch, configuration checks."""

import pytest
from fastapi.testclient import TestClient

from src.backend.app import create_app
from src.backend.config import Settings, load_settings
from src.backend.security import MAX_BODY_BYTES, SECURITY_HEADERS
from tests.fakes import FakeMailer


VALID = {"name": "Erika", "email": "erika@example.org", "message": "Hallo, eine Testnachricht."}


# Response headers


@pytest.mark.parametrize("path", ["/", "/contact.html", "/does-not-exist.html"])
def test_pages_send_security_headers(client, path):
    response = client.get(path)

    for name, value in SECURITY_HEADERS.items():
        assert response.headers.get(name) == value, name


def test_api_responses_send_security_headers(client):
    response = client.post("/api/contact", json=VALID)

    assert response.status_code == 200
    assert response.headers["x-content-type-options"] == "nosniff"
    assert "content-security-policy" in response.headers


def test_content_security_policy_forbids_inline_code_and_framing():
    policy = SECURITY_HEADERS["content-security-policy"]

    assert "unsafe-inline" not in policy
    assert "unsafe-eval" not in policy
    assert "frame-ancestors 'none'" in policy
    assert "script-src 'self'" in policy


# Request size limit


def test_large_body_is_rejected_before_reading(client, mailer):
    response = client.post(
        "/api/contact",
        content=b"x" * (MAX_BODY_BYTES + 1),
        headers={"content-type": "application/json"},
    )

    assert response.status_code == 413
    assert response.json() == {"detail": "request_too_large"}
    assert response.headers["x-content-type-options"] == "nosniff"
    assert mailer.sent == []


def test_large_chunked_body_without_content_length_is_rejected(client, mailer):
    chunks = (b"x" * 16_384 for _ in range(MAX_BODY_BYTES // 16_384 + 2))

    response = client.post("/api/contact", content=chunks, headers={"content-type": "application/json"})

    assert response.status_code == 413
    assert mailer.sent == []


def test_normal_request_is_not_affected(client, mailer):
    assert client.post("/api/contact", json={**VALID, "message": "x" * 5000}).status_code == 200
    assert len(mailer.sent) == 1


# API docs


def test_api_docs_are_off_in_production(client):
    assert client.get("/api/docs").status_code == 404
    assert client.get("/api/openapi.json").status_code == 404


def test_api_docs_are_on_in_development():
    settings = Settings("j@example.com", "w@example.com", environment="development")
    with TestClient(create_app(settings, mailer=FakeMailer())) as client:
        docs = client.get("/api/docs")
        assert docs.status_code == 200
        # Swagger UI needs inline scripts from a CDN, so the docs page is exempt from the CSP.
        assert "content-security-policy" not in docs.headers
        assert client.get("/api/openapi.json").status_code == 200


# Configuration


ENV_VARS = [
    "APP_ENV",
    "SMTP_HOST",
    "SMTP_PORT",
    "SMTP_SECURITY",
    "SMTP_USERNAME",
    "SMTP_PASSWORD",
    "CONTACT_RECIPIENT",
    "CONTACT_SENDER",
]


@pytest.fixture
def env(monkeypatch):
    for name in ENV_VARS:
        monkeypatch.delenv(name, raising=False)

    def set_env(**values):
        for name, value in values.items():
            monkeypatch.setenv(name, value)

    return set_env


def test_production_without_mail_server_refuses_to_start(env):
    with pytest.raises(RuntimeError, match="SMTP_HOST is not set"):
        load_settings()


def test_development_without_mail_server_uses_the_console(env):
    env(APP_ENV="development")

    settings = load_settings()

    assert settings.smtp is None
    assert settings.is_development


def test_unknown_environment_is_rejected(env):
    env(APP_ENV="staging")

    with pytest.raises(RuntimeError, match="APP_ENV"):
        load_settings()


def test_unencrypted_smtp_login_is_refused(env):
    env(
        SMTP_HOST="mail.example.com",
        SMTP_SECURITY="none",
        SMTP_USERNAME="website",
        SMTP_PASSWORD="secret",
        CONTACT_RECIPIENT="j@example.com",
        CONTACT_SENDER="w@example.com",
    )

    with pytest.raises(RuntimeError, match="unencrypted"):
        load_settings()


def test_production_with_mail_server(env):
    env(
        SMTP_HOST="mail.example.com",
        SMTP_SECURITY="ssl",
        SMTP_USERNAME="website",
        SMTP_PASSWORD="secret",
        CONTACT_RECIPIENT="j@example.com",
        CONTACT_SENDER="w@example.com",
    )

    settings = load_settings()

    assert not settings.is_development
    assert settings.smtp.port == 465
    assert settings.smtp.security == "ssl"
