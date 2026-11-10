# Deployment

Because of the contact form, the site needs a host that can run Python. The FastAPI app serves
both the pages and the API, so a single process is enough:

```bash
uv sync --frozen --no-dev
APP_ENV=production uv run --no-sync uvicorn src.backend.main:app --host 127.0.0.1 --port 8000 \
    --proxy-headers --forwarded-allow-ips 127.0.0.1 --no-server-header
```

Run it behind a reverse proxy (e.g. nginx or Caddy) that handles HTTPS. `--proxy-headers` makes
the rate limiter see the visitor's IP instead of the proxy's. Run **one** worker process: the
rate limiter keeps its counts in memory per process. Only allow `127.0.0.1` (the proxy) in
`--forwarded-allow-ips`, never `*`: otherwise visitors could fake their IP and bypass the rate
limit. `--no-server-header` hides the uvicorn version.

The app sends its own security headers (CSP etc., see
[Architecture](architecture.md#security)). On the proxy, additionally:

- redirect HTTP to HTTPS and send `Strict-Transport-Security: max-age=31536000` (HSTS)
- optionally limit request bodies there too (e.g. nginx `client_max_body_size 64k;`)

Hosting has not been chosen yet.

## Configuration

Set these environment variables (or a `.env` file in the repository root, see `.env.example`):

- `APP_ENV=production` (also the default): requires a mail server and turns off the API docs.
  Never use `development` on the server — it prints messages to the log instead of sending them.
- `SMTP_HOST`, `SMTP_PORT`, `SMTP_SECURITY` (`starttls`, `ssl` or `none`), `SMTP_USERNAME`,
  `SMTP_PASSWORD`: the mail account that sends the contact messages
- `CONTACT_RECIPIENT`: where messages are delivered
- `CONTACT_SENDER`: the From address; must be allowed by the mail server (usually the account)

In production the app refuses to start without `SMTP_HOST`, without `CONTACT_RECIPIENT` or
`CONTACT_SENDER`, or with `SMTP_SECURITY=none` plus a username/password (which would be sent
unencrypted). Send a test message after deploying.

## Before going live

- Replace all placeholder content (texts, contact data, images, alt texts).
- Fill in `impressum.html` and `datenschutz.html`, have them checked legally, then remove the
  yellow "Entwurf" notice and the `noindex` meta tag from both pages.
- Describe the chosen host and its server logs in section 2 of the Datenschutzerklärung, and the
  mail provider in section 3 (contact form).
- Release from `main` only (see [Development](development.md#git-workflow)).
