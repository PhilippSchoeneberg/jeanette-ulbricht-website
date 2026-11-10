# Architecture

Five HTML pages with shared CSS and small scripts, served by a small FastAPI backend that also
handles the contact form. No frontend framework, no build step, no third-party resources (fonts,
analytics, embeds).

## Directory layout

```
src/
├── frontend/
│   ├── index.html          Portfolio (landing page)
│   ├── biography.html      Biografie
│   ├── contact.html        Kontakt
│   ├── impressum.html      Impressum (draft placeholder)
│   ├── datenschutz.html    Datenschutzerklärung (draft placeholder)
│   ├── css/
│   │   ├── base.css        Design tokens, reset, typography, buttons, nav, footer, shared components
│   │   ├── home.css        Project tiles, gallery carousel, call to action
│   │   ├── biography.css   Portrait, focus areas, career timeline
│   │   ├── contact.css     Contact cards and contact form
│   │   └── legal.css       Impressum / Datenschutz
│   ├── js/
│   │   ├── head.js         Theme and language before first paint (every page, no defer)
│   │   ├── i18n.js         Language switching (every page)
│   │   ├── main.js         Theme toggle, mobile navigation, scroll reveal (every page)
│   │   ├── gallery.js      Draggable image carousel (portfolio page)
│   │   └── contact-form.js Contact form validation and sending (contact page)
│   ├── locales/
│   │   ├── de.json         German texts (same as in the HTML)
│   │   └── en.json         English translations
│   └── assets/
│       ├── favicon.ico
│       └── images/         Placeholder images
└── backend/
    ├── main.py             Entry point (`uvicorn src.backend.main:app`)
    ├── app.py              App factory: API routes + static frontend
    ├── config.py           Settings from environment variables / `.env`
    ├── routers/contact.py  POST /api/contact
    ├── schemas.py          Request validation (Pydantic)
    ├── mailer.py           SMTP mailer; console mailer for development
    ├── rate_limit.py       In-memory rate limiter
    └── security.py         Request size limit, security headers (CSP)
tests/                      Backend and translation tests (pytest)
└── e2e/                    Browser tests (Playwright, headless Chromium)
doc/                        This documentation
```

## Pages

Every page loads `css/base.css` plus its own stylesheet, and `js/main.js`. The global navigation
and footer are repeated in each HTML file (there is no templating), so changes to them must be
made in all five pages. Each page marks its own navigation link with `aria-current="page"`.

## Design

Apple-inspired: light and dark tiles, large semibold headlines, pill-shaped buttons, a dark
translucent sticky navigation bar and a light grey footer. Colours, spacing and radii are CSS
custom properties at the top of `css/base.css`. Fonts are the visitor's system fonts.

Light and dark themes: the colour tokens have a light set (default) and a dark set. The dark set
applies when `<html data-theme="dark">` is set, or, without JavaScript, when the system prefers
dark mode. A small inline script in each page's `<head>` sets `data-theme` before first paint
(saved choice from `localStorage` key `theme`, otherwise the system preference), so there is no
flash of the wrong theme. The sun/moon button in the navigation (`js/main.js`) switches the theme
and saves the choice; without a saved choice the site follows system changes live.

## Languages

The site is German with an English translation. German is written directly in the HTML, so the
pages work without JavaScript and search engines see German. Translatable elements carry keys:

- `data-i18n="key"`: the element's text (elements with this attribute contain text only)
- `data-i18n-<attribute>="key"`: an attribute, e.g. `data-i18n-alt`, `data-i18n-aria-label`,
  `data-i18n-content` (meta description)

`js/i18n.js` loads `locales/<code>.json` and applies the texts. Scripts use `window.i18n.t(key)`
for texts they create (form messages, button labels) and re-render on the `languagechange`
event. The "EN"/"DE" button in the navigation switches the language and saves the choice in
`localStorage` (`language`); otherwise the browser language decides (German or English, else
German). The inline `<head>` script picks the language before first paint and hides the page
while a non-German translation loads (at most 1.5 s).

The Impressum and Datenschutzerklärung stay German in every language (the German version is the
legally relevant one); in English they show a note saying so. Only their navigation, footer and
headings are translated.

`tests/test_locales.py` checks that both locale files have the same keys, that every key used in
the pages and scripts exists, that no key is unused, and that `de.json` matches the German text
in the HTML.

Breakpoints: 1068px and 734px for layout and type, 834px for the mobile navigation menu.

## Gallery carousel

`js/gallery.js` moves the image track with the Web Animations API (1200 ms, `fill: "forwards"`)
and shifts each image's `object-position` at the same time for a parallax effect. Input:

- drag with mouse, touch or pen (Pointer Events)
- horizontal scrolling: trackpad swipe, tilt wheel, Shift + mouse wheel
- keyboard: arrow keys, Home / End (the carousel is focusable)
- previous / next buttons

With `prefers-reduced-motion` the movement is instant and the parallax is off.

## Backend and contact form

`create_app(settings)` builds the FastAPI app: the API under `/api` and, for every other path,
the static files from `src/frontend` (so `/` serves `index.html`). Interactive API docs are at
`/api/docs` in development only; see [API](api.md).

The contact form (`contact.html`, `js/contact-form.js`) validates in the browser and sends JSON
to `POST /api/contact`. The backend validates again, then e-mails the message to
`CONTACT_RECIPIENT` via SMTP, with the visitor as `Reply-To`. **Messages are not stored.**
Without `SMTP_HOST` the e-mail is printed to the console instead, but only with
`APP_ENV=development`; in production (the default) the app refuses to start without a mail server.

Spam protection:

- a hidden honeypot field (`website`); if filled, the request "succeeds" but nothing is sent
- at most 5 messages per client IP per 15 minutes, counted in memory (per server process)

## Security

`src/backend/security.py` adds two middlewares to every response, pages and API alike:

- **Request size limit**: bodies over 64 KB get a 413 before they are read into memory (also for
  chunked requests without `Content-Length`).
- **Security headers**: a strict Content Security Policy (only the site's own scripts, styles,
  images and translations; no inline scripts or styles, no `eval`, no third parties, no framing),
  plus `X-Content-Type-Options: nosniff`, `X-Frame-Options: DENY`, `Referrer-Policy`,
  `Permissions-Policy` and cross-origin policies. The development-only `/api/docs` page is exempt
  from the CSP, since Swagger UI loads from a CDN.

Because of the CSP, the script that has to run before the first paint (theme and language) is a
separate file, `js/head.js`, loaded without `defer` — not an inline `<script>`. New external
resources, inline scripts or inline `style` attributes would be blocked: change the policy in
`security.py` deliberately if one is ever needed. `tests/test_security.py` and
`tests/e2e/test_content_security_policy.py` check the headers and that pages work without CSP
violations.

Other protections: the API only accepts JSON (so other sites can't submit the form on a visitor's
behalf), name and subject can't contain line breaks (no e-mail header injection), the recipient is
fixed (no open relay), the frontend never builds HTML from data (`textContent` only), and stored
preferences are whitelisted. CI actions are pinned to commit SHAs and Dependabot proposes updates
(`.github/dependabot.yml`).

## Roadmap

Not decided yet:

- Project detail views (lightbox or project pages)
- Real content and optimised images (WebP/AVIF, `srcset`)
- Open Graph tags
- `mailto:` / `tel:` links once real contact data exists
- Stronger spam protection, only if spam becomes a problem
