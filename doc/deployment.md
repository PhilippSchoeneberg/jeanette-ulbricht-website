# Deployment

Because of the contact form, the site needs a host that can run Python. The FastAPI app serves
both the pages and the API, so a single process is enough:

```bash
pip install -r requirements.txt
uvicorn src.backend.main:app --host 127.0.0.1 --port 8000 --proxy-headers --forwarded-allow-ips 127.0.0.1
```

Run it behind a reverse proxy (e.g. nginx or Caddy) that handles HTTPS. `--proxy-headers` makes
the rate limiter see the visitor's IP instead of the proxy's. Run **one** worker process: the
rate limiter keeps its counts in memory per process.

Hosting has not been chosen yet.

## Configuration

Set these environment variables (or a `.env` file in the repository root, see `.env.example`):

- `SMTP_HOST`, `SMTP_PORT`, `SMTP_SECURITY` (`starttls`, `ssl` or `none`), `SMTP_USERNAME`,
  `SMTP_PASSWORD`: the mail account that sends the contact messages
- `CONTACT_RECIPIENT`: where messages are delivered
- `CONTACT_SENDER`: the From address; must be allowed by the mail server (usually the account)

With `SMTP_HOST` set, the app refuses to start if `CONTACT_RECIPIENT` or `CONTACT_SENDER` is
missing. Send a test message after deploying.

## Before going live

- Replace all placeholder content (texts, contact data, images, alt texts).
- Fill in `impressum.html` and `datenschutz.html`, have them checked legally, then remove the
  yellow "Entwurf" notice and the `noindex` meta tag from both pages.
- Describe the chosen host and its server logs in section 2 of the Datenschutzerklärung, and the
  mail provider in section 3 (contact form).
- Release from `main` only (see [Development](development.md#git-workflow)).
