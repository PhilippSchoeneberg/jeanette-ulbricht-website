"""Browser test fixtures: the real FastAPI app served by uvicorn, driven by Playwright.

The server runs in a background thread on a free local port, with a fake mailer, so no mail
server is needed. Every test gets a fresh browser context (empty localStorage) in German, light
mode and with reduced motion, so animations finish instantly and results don't depend on the
machine running the tests.
"""

import json
import socket
import threading
import time
from pathlib import Path

import pytest
import uvicorn
from tests.fakes import FakeMailer

from src.backend.app import create_app
from src.backend.config import FRONTEND_DIR, Settings


E2E_DIR = Path(__file__).parent


def pytest_collection_modifyitems(items):
    # Mark every browser test, so `pytest -m "not e2e"` runs only the fast API tests.
    for item in items:
        if E2E_DIR in Path(item.fspath).parents:
            item.add_marker(pytest.mark.e2e)


def _free_port():
    with socket.socket() as sock:
        sock.bind(("127.0.0.1", 0))
        return sock.getsockname()[1]


@pytest.fixture(scope="session")
def server_mailer():
    return FakeMailer()


@pytest.fixture(scope="session")
def live_server(server_mailer):
    settings = Settings(
        contact_recipient="jeanette@example.com",
        contact_sender="website@example.com",
        # The rate limit itself is covered by the API tests; don't let it interfere here.
        rate_limit_count=1000,
    )
    app = create_app(settings, mailer=server_mailer)
    port = _free_port()
    server = uvicorn.Server(uvicorn.Config(app, host="127.0.0.1", port=port, log_level="warning", ws="none"))
    thread = threading.Thread(target=server.run, daemon=True)
    thread.start()

    deadline = time.monotonic() + 10
    while not server.started:
        if not thread.is_alive() or time.monotonic() > deadline:
            raise RuntimeError("The test server did not start.")
        time.sleep(0.05)

    yield f"http://127.0.0.1:{port}"

    server.should_exit = True
    thread.join(timeout=5)


@pytest.fixture(scope="session")
def base_url(live_server):
    # Used by pytest-playwright: page.goto("/contact.html") resolves against it.
    return live_server


@pytest.fixture(scope="session")
def browser_context_args(browser_context_args):
    return {
        **browser_context_args,
        "locale": "de-DE",
        "color_scheme": "light",
        "reduced_motion": "reduce",
        "viewport": {"width": 1280, "height": 800},
    }


@pytest.fixture
def mailer(server_mailer):
    server_mailer.sent.clear()
    server_mailer.fail = False
    return server_mailer


def _load_locale(code):
    return json.loads((FRONTEND_DIR / "locales" / f"{code}.json").read_text(encoding="utf-8"))


@pytest.fixture(scope="session")
def de():
    return _load_locale("de")


@pytest.fixture(scope="session")
def en():
    return _load_locale("en")
