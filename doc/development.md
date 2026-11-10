# Development

## Setup

Requires Python 3.11 or newer.

```bash
python3 -m venv .venv
.venv/bin/pip install -r requirements-dev.txt
cp .env.example .env
```

For local development, leave `SMTP_HOST` in `.env` empty: contact form messages are then printed
to the server console instead of being sent. To test real sending, fill in the SMTP settings
(see `.env.example`).

## Run

From the repository root:

```bash
.venv/bin/uvicorn src.backend.main:app --reload
```

Open http://127.0.0.1:8000. The API docs are at http://127.0.0.1:8000/api/docs.

The frontend has no build step: edit files in `src/frontend` and reload the page. Without the
backend (e.g. `python3 -m http.server 8000 --directory src/frontend`) all pages work except
sending the contact form.

## Tests

```bash
.venv/bin/pytest
```

The tests run the real FastAPI app with a fake mailer, so they need no mail server and no `.env`.

## Check before committing

Run the tests. The frontend has no automated tests: check changes in a browser at desktop width
and at phone width (about 375px), in light and dark mode, on every page you touched. For the
portfolio page, also check that the gallery can be dragged, scrolled sideways and moved with the
keyboard; for the contact page, send a test message (it appears in the server console).

## Content

All texts, contact data and images are placeholders. Don't invent real content: biography,
projects and contact data come from Jeanette Ulbricht.

Images live in `src/frontend/assets/images/`. Scale photos to about 1600px height before adding
them (for example with `sips --resampleHeight 1600` on macOS) and set `width` / `height` on the
`<img>`.

## Git workflow

- `main`: release versions only. `development`: integration branch and the default branch.
- No direct commits to `main` or `development`. Work on a feature branch created from
  `development` (`feature/<name>`, `fix/<name>`).
- Feature branches are merged into `development` through pull requests; `development` is merged
  into `main` for a release.
