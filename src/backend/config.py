"""Settings, read from environment variables (and `.env` in the repository root)."""

import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv


ROOT_DIR = Path(__file__).resolve().parents[2]
FRONTEND_DIR = ROOT_DIR / "src" / "frontend"

load_dotenv(ROOT_DIR / ".env")

SMTP_SECURITY_MODES = ("starttls", "ssl", "none")

# "production" (the default, so a forgotten setting fails safe) or "development".
APP_ENVIRONMENTS = ("production", "development")


@dataclass(frozen=True)
class SmtpSettings:
    host: str
    port: int
    username: str
    password: str
    security: str  # one of SMTP_SECURITY_MODES


@dataclass(frozen=True)
class Settings:
    # Where contact form messages go and which address they are sent from.
    contact_recipient: str
    contact_sender: str
    # None: no mail server configured, messages are printed to the console (development only).
    smtp: SmtpSettings | None = None
    # Spam protection: at most this many messages per client IP within the window.
    rate_limit_count: int = 5
    rate_limit_window_seconds: int = 15 * 60
    # One of APP_ENVIRONMENTS. Development enables the console mailer and the API docs.
    environment: str = "production"

    @property
    def is_development(self) -> bool:
        return self.environment == "development"


def _get(name, default=""):
    return os.environ.get(name, default).strip()


def _require(name):
    value = _get(name)
    if not value:
        raise RuntimeError(f"Environment variable {name} is not set. Copy .env.example to .env and fill it in.")
    return value


def load_settings():
    environment = _get("APP_ENV", "production").lower()
    if environment not in APP_ENVIRONMENTS:
        raise RuntimeError(f"APP_ENV must be one of {', '.join(APP_ENVIRONMENTS)}.")

    smtp_host = _get("SMTP_HOST")
    if not smtp_host:
        if environment != "development":
            # Without this check a forgotten setting on the server would tell visitors "sent"
            # while their messages only end up in the server log.
            raise RuntimeError(
                "SMTP_HOST is not set. In production the contact form needs a mail server. "
                "For local development set APP_ENV=development to print messages to the console instead."
            )
        # Development: nothing is sent, so placeholder addresses are fine.
        return Settings(
            contact_recipient=_get("CONTACT_RECIPIENT") or "kontakt@example.com",
            contact_sender=_get("CONTACT_SENDER") or "website@example.com",
            environment=environment,
        )

    security = _get("SMTP_SECURITY", "starttls").lower()
    if security not in SMTP_SECURITY_MODES:
        raise RuntimeError(f"SMTP_SECURITY must be one of {', '.join(SMTP_SECURITY_MODES)}.")

    username = _get("SMTP_USERNAME")
    password = _get("SMTP_PASSWORD")
    if security == "none" and (username or password):
        raise RuntimeError(
            "SMTP_SECURITY=none would send SMTP_USERNAME/SMTP_PASSWORD unencrypted. Use starttls or ssl."
        )

    return Settings(
        contact_recipient=_require("CONTACT_RECIPIENT"),
        contact_sender=_require("CONTACT_SENDER"),
        smtp=SmtpSettings(
            host=smtp_host,
            port=int(_get("SMTP_PORT", "465" if security == "ssl" else "587")),
            username=username,
            password=password,
            security=security,
        ),
        environment=environment,
    )
