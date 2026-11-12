# Deployment

The site runs as a Docker container on an Oracle Cloud server (Ubuntu, arm64 / Ampere A1),
next to other projects. A separate Caddy container (`/opt/proxy`, not part of this repository)
is the only container with public ports 80/443: it terminates HTTPS (Let's Encrypt certificates),
redirects HTTP to HTTPS and forwards requests as plain HTTP over the Docker network `web`.

```
visitor --HTTPS--> Caddy (/opt/proxy, ports 80/443) --HTTP over network "web"--> jeanette-ulbricht-website:8000
```

## Files

- `Dockerfile`: multi-stage build. Stage 1 installs the locked dependencies (`uv.lock`) with uv;
  the final image (`python:3.13-slim`, multi-arch, also arm64) contains only Python, the virtual
  environment and `src/`. Runs as the unprivileged user `app`, listens on `0.0.0.0:8000`, has a
  health check (`docker ps` shows `healthy`).
- `compose.yaml`: one service, container name `jeanette-ulbricht-website`, `restart:
  unless-stopped`, joins the external network `web`. **No `ports:`**, so the app is only
  reachable through Caddy, i.e. only over HTTPS. Always `APP_ENV=production`. Hardened: read-only
  filesystem, no Linux capabilities, no privilege escalation, 256 MB memory limit, rotated logs.
- `.env` (not committed, see `.env.example`): mail settings.

**No persistent data:** contact messages are e-mailed, not stored, so there is no volume and
nothing to back up apart from `.env`.

## HTTPS behind Caddy

- The app has no TLS and no HTTP-to-HTTPS redirect of its own (Caddy does both; a second
  redirect would cause loops).
- uvicorn runs with `--proxy-headers`: it trusts `X-Forwarded-For` and `X-Forwarded-Proto` from
  the addresses in `FORWARDED_ALLOW_IPS` (default: Docker's private address ranges), so the rate
  limit sees the visitor's IP and the app knows the request was HTTPS. Caddy passes the original
  `Host` header through. To trust only the `web` network, set its subnet in `.env`
  (`docker network inspect web --format '{{(index .IPAM.Config 0).Subnet}}'`).
- All links and asset URLs in the site are relative; there is no `http://` anywhere and no
  cookies, base-URL, allowed-hosts or CORS setting to configure.
- The app sends its own security headers (CSP etc., see [Architecture](architecture.md#security));
  Caddy adds HSTS.

## Caddy site block

In `/opt/proxy/Caddyfile`:

```
jeanette-ulbricht.duckdns.org {
    encode zstd gzip
    header Strict-Transport-Security "max-age=31536000"
    header -Server
    request_body {
        max_size 64KB
    }
    reverse_proxy jeanette-ulbricht-website:8000
}
```

## Deploy

```bash
git clone -b main https://github.com/PhilippSchoeneberg/jeanette-ulbricht-website.git /opt/jeanette-ulbricht-website
cd /opt/jeanette-ulbricht-website
cp .env.example .env && nano .env      # fill in the SMTP_* and CONTACT_* settings
docker compose up -d --build
docker ps --filter name=jeanette-ulbricht-website   # wait for "healthy"
```

Then add the Caddy block above and reload Caddy, open `https://jeanette-ulbricht.duckdns.org` and send a test
message through the contact form.

Update after a new release on `main`:

```bash
cd /opt/jeanette-ulbricht-website && git pull && docker compose up -d --build
```

## Configuration

Set in `.env` (see `.env.example`):

- `SMTP_HOST`, `SMTP_PORT`, `SMTP_SECURITY` (`starttls`, `ssl` or `none`), `SMTP_USERNAME`,
  `SMTP_PASSWORD`: the mail account that sends the contact messages
- `CONTACT_RECIPIENT`: where messages are delivered
- `CONTACT_SENDER`: the From address; must be allowed by the mail server (usually the account)
- optional `FORWARDED_ALLOW_IPS`: which addresses may send proxy headers (see above)

`APP_ENV` is always `production` in the container (set in `compose.yaml`): a mail server is
required and the API docs are off. The app refuses to start without `SMTP_HOST`, without
`CONTACT_RECIPIENT` or `CONTACT_SENDER`, or with `SMTP_SECURITY=none` plus a username/password
(which would be sent unencrypted) — `docker compose logs` shows the reason. Run **one** worker
process (the default): the rate limiter keeps its counts in memory per process.

## Without Docker

The same app can run directly: `uv sync --frozen --no-dev`, then
`APP_ENV=production uv run --no-sync uvicorn src.backend.main:app --host 127.0.0.1 --port 8000
--proxy-headers --forwarded-allow-ips 127.0.0.1 --no-server-header` behind any HTTPS reverse proxy.
Only allow the proxy's address in `--forwarded-allow-ips`, never `*`.

## Before going live

- Release: merge `development` into `main` (the server deploys `main`).
- Replace all placeholder content (texts, contact data, images, alt texts).
- Fill in `impressum.html` and `datenschutz.html`, have them checked legally, then remove the
  yellow "Entwurf" notice and the `noindex` meta tag from both pages.
- Describe the hosting (Oracle Cloud, server logs, Caddy) in section 2 of the
  Datenschutzerklärung, and the mail provider in section 3 (contact form).
