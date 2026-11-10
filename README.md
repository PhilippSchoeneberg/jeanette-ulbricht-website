# Jeanette Ulbricht – Website

Portfolio website for Jeanette Ulbricht, media designer (Mediengestalterin): her work, a short
biography, contact details and a contact form. The site is in German.

- Frontend: plain HTML, CSS and JavaScript (`src/frontend`), no build step
- Backend: Python with FastAPI (`src/backend`); serves the frontend and sends contact form
  messages by e-mail

The site is a **draft**: design and structure are in place, all content (texts, contact data,
images) is placeholder, and the Impressum and Datenschutz pages still have to be filled in.

## Quick start

```bash
python3 -m venv .venv
```
```bash
.venv/bin/pip install -r requirements-dev.txt
```
```bash
cp .env.example .env        # leave SMTP_HOST empty to print contact messages to the console
```
```bash
.venv/bin/uvicorn src.backend.main:app --reload
```

Then open http://127.0.0.1:8000.

Run the tests with `.venv/bin/pytest`.

## Documentation

- [Architecture](doc/architecture.md)
- [API](doc/api.md)
- [Development](doc/development.md)
- [Deployment](doc/deployment.md)
