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
│   │   ├── main.js         Theme toggle, mobile navigation, scroll reveal (every page)
│   │   ├── gallery.js      Draggable image carousel (portfolio page)
│   │   └── contact-form.js Contact form validation and sending (contact page)
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
    └── rate_limit.py       In-memory rate limiter
tests/                      Backend tests (pytest)
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
`/api/docs`; see [API](api.md).

The contact form (`contact.html`, `js/contact-form.js`) validates in the browser and sends JSON
to `POST /api/contact`. The backend validates again, then e-mails the message to
`CONTACT_RECIPIENT` via SMTP, with the visitor as `Reply-To`. **Messages are not stored.**
Without `SMTP_HOST` (local development) the e-mail is printed to the console instead.

Spam protection:

- a hidden honeypot field (`website`); if filled, the request "succeeds" but nothing is sent
- at most 5 messages per client IP per 15 minutes, counted in memory (per server process)

## Roadmap

Not decided yet:

- Project detail views (lightbox or project pages)
- Real content and optimised images (WebP/AVIF, `srcset`)
- Open Graph tags
- `mailto:` / `tel:` links once real contact data exists
- Stronger spam protection, only if spam becomes a problem
