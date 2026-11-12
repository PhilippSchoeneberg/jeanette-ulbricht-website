# Jeanette Ulbricht – Website

Portfolio website for Jeanette Ulbricht, media designer (Mediengestalterin): her work, a short
biography, contact details and a contact form. The site is in German.

- Frontend: plain HTML, CSS and JavaScript (`src/frontend`), no build step
- Backend: Python with FastAPI (`src/backend`); serves the frontend and sends contact form
  messages by e-mail

The site is a **draft**: design and structure are in place, all content (texts, contact data,
images) is placeholder, and the Impressum and Datenschutz pages still have to be filled in.

## Quick start

Needs [uv](https://docs.astral.sh/uv/) (`brew install uv`).

```bash
uv sync
```
```bash
cp .env.example .env        # APP_ENV=development: contact messages are printed to the console
```
```bash
uv run uvicorn src.backend.main:app --reload
```

Then open http://127.0.0.1:8000.

Run the tests with `uv run pytest` and the linter with `uv run ruff check .`. The browser tests
(Playwright, `tests/e2e`) need Chromium once: `uv run playwright install chromium`. GitHub Actions
runs both on every pull request into
`development` or `main`; merging requires them to pass (see [Development](doc/development.md#continuous-integration)).

## Documentation

- [Architecture](doc/architecture.md)
- [API](doc/api.md)
- [Development](doc/development.md)
- [Deployment](doc/deployment.md) (Docker on the server, behind Caddy)
