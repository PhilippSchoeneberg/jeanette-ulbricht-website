from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from .config import FRONTEND_DIR, Settings
from .mailer import ConsoleMailer, SmtpMailer
from .rate_limit import RateLimiter
from .routers import contact


def create_app(settings: Settings, mailer=None):
    """Builds the app. Tests pass their own `mailer`; otherwise it follows the settings."""
    app = FastAPI(
        title="Jeanette Ulbricht – Website",
        docs_url="/api/docs",
        redoc_url=None,
        openapi_url="/api/openapi.json",
    )

    app.state.settings = settings
    app.state.mailer = mailer or (SmtpMailer(settings.smtp) if settings.smtp else ConsoleMailer())
    app.state.rate_limiter = RateLimiter(settings.rate_limit_count, settings.rate_limit_window_seconds)

    app.include_router(contact.router)

    # Everything that isn't an API route is the static frontend.
    app.mount("/", StaticFiles(directory=FRONTEND_DIR, html=True), name="frontend")

    return app
