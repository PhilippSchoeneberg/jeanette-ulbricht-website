# CLAUDE.md

Guidance for Claude Code when working in this repository.

## Project

Portfolio homepage for **Jeanette Ulbricht**, a media designer (Mediengestalterin). The site presents her work (portfolio), a short biography, contact details and a contact form. Audience: potential clients and employers, mostly German-speaking.

The site is a **draft**: structure and design are in place, content is placeholder. Improving structure is welcome as long as the visual identity (see below) is kept unless the user asks otherwise.

- Site language: **German** (navigation, headings, copy), with an **English translation** via a language switch. German stays in the HTML; every translatable text needs a `data-i18n` / `data-i18n-<attr>` key with identical German in `locales/de.json` and English in `locales/en.json` (`tests/test_locales.py` enforces this). Impressum and Datenschutz content stays German only. Code, comments and commit messages: English.
- Author/maintainer: Philipp Schöneberg (`<meta name="author">`).
- Placeholder content everywhere: Lorem-ipsum biography, masked e-mail/phone, stock example images. Never invent real contact data, biography facts or project descriptions; leave clear placeholders and ask.

## Tech stack

- Frontend: **HTML, CSS, vanilla JavaScript** — no build step, no framework, no npm.
- Backend: **Python 3.11+ with FastAPI** (`src/backend`). It serves the frontend as static files and provides `POST /api/contact`, which e-mails contact form messages via SMTP (nothing is stored). Dependencies are managed with **uv** (as in FormelX): declared in `pyproject.toml` (`[dependency-groups] dev` for test tools), pinned in `uv.lock` — commit both, add packages with `uv add` / `uv add --dev` (ask the user first). Structure follows the user's FormelX project (`create_app(settings)` factory, settings from `.env`).
- Tests: pytest (`tests/`, fake mailer, no mail server needed) — API and translation tests in `tests/test_*.py`, browser tests with Playwright (`pytest-playwright`, headless Chromium) in `tests/e2e/` covering the gallery, theme toggle, language switch, mobile nav and contact form. Update the browser tests when changing that behaviour; `pytest -m "not e2e"` skips them.
- Lint/format: ruff (config under `[tool.ruff]` in `pyproject.toml`): `uv run ruff check .` and `uv run ruff format .` — two blank lines after imports (house style).

Setup and run from the repository root:

```bash
uv sync
uv run playwright install chromium     # browser for tests/e2e (once)
cp .env.example .env     # SMTP_HOST empty = contact messages printed to the console
uv run uvicorn src.backend.main:app --reload
uv run pytest                          # all tests; -m "not e2e" skips the browser tests
uv run pytest tests/e2e --headed       # watch the browser tests
```

Project documentation lives in `doc/` (architecture, api, development, deployment) and the `README.md`. Keep them in sync when changing structure, API, workflow or run commands.

Don't introduce a frontend framework, bundler or npm dependencies, or new Python dependencies, without asking the user first. Never commit `.env`.

## File layout

| File | Purpose |
| --- | --- |
| `src/frontend/index.html` / `css/home.css` | Portfolio (landing page): hero tile, project tiles, gallery carousel, call to action |
| `src/frontend/biography.html` / `css/biography.css` | Biography: portrait + text, focus-area cards, career timeline |
| `src/frontend/contact.html` / `css/contact.css` / `js/contact-form.js` | Contact cards (e-mail, phone) and contact form (client-side validation, sends JSON to `/api/contact`) |
| `src/frontend/impressum.html`, `datenschutz.html` / `css/legal.css` | Legal pages — **draft placeholders only**, marked "nicht veröffentlichen" |
| `src/frontend/css/base.css` | Design tokens (CSS custom properties), reset, typography, buttons, global nav, footer, shared components (page hero, sections, cards, scroll reveal) |
| `src/frontend/js/i18n.js`, `src/frontend/locales/{de,en}.json` | Language switching (German/English): `data-i18n` keys in the HTML, `window.i18n.t()` for script texts, `languagechange` event |
| `src/frontend/js/main.js` | Light/dark theme toggle, mobile navigation menu, scroll-reveal (IntersectionObserver); loaded on every page |
| `src/frontend/js/gallery.js` | Draggable image track with parallax (Pointer Events, horizontal wheel/trackpad, keyboard, prev/next buttons) |
| `src/frontend/assets/favicon.ico` | Favicon |
| `src/frontend/assets/images/exampleSet0/` | Profile picture placeholder |
| `src/frontend/assets/images/exampleSet1/` | Portfolio placeholder images (`image0–7.jpg`, 1600px high) |
| `src/backend/` | FastAPI app: `main.py` (entry), `app.py` (factory, static mount), `config.py` (env settings), `routers/contact.py`, `schemas.py`, `mailer.py` (SMTP / console), `rate_limit.py` |
| `tests/` | pytest: API/translation tests (`test_*.py`, `conftest.py`), shared `fakes.py` (fake mailer) |
| `tests/e2e/` | Playwright browser tests; `conftest.py` starts the app with uvicorn on a free port (fake mailer) |
| `pyproject.toml`, `uv.lock`, `.env.example` | Python dependencies (uv), pytest and ruff config; lock file; config template |
| `doc/` | Architecture, development and deployment docs |
| `.claude/launch.json` | Local preview config (runs the FastAPI app with uvicorn on port 8000; needs `.venv`) |

All paths inside the pages are relative to `src/frontend/`. Every page repeats the same `<head>` (including the inline theme script), global nav (`.global-nav`) and footer (`.global-footer`) markup — there is no templating. Changes to nav/footer must be applied to **all five pages**. Each page sets `aria-current="page"` on its own nav link.

## Visual identity (current design)

Redesigned in an Apple-inspired style (clean, light, large type, tiles). Only the design language is borrowed — no Apple logos, product names, images or font files.

- Colours (tokens in `src/frontend/css/base.css`): white / light grey `#f5f5f7` / black tiles, text `#1d1d1f`, secondary text `#6e6e73`, accent blue `#0071e3` for buttons and `#0066cc` for links.
- Light and dark theme: dark tokens apply via `<html data-theme="dark">` or, without JS, `prefers-color-scheme: dark`. An inline `<head>` script on every page sets `data-theme` before paint (saved `localStorage` "theme", else system preference); the sun/moon `.theme-toggle` in the nav switches and saves it. New colours must be tokens with a value in **both** the light and dark sets (the dark set appears twice in `base.css`: explicit choice and system preference — keep them identical).
- Font: system font stack (`system-ui, -apple-system, …`) — nothing loaded from third parties.
- Global nav: 48px sticky, dark translucent bar with blur; name left, links right (Biografie · Portfolio · Kontakt); full-screen menu with a two-bar toggle below 834px.
- Large centred headlines (hero 80px, sections 48px, semibold), section headlines with a grey second sentence ("Weitere Arbeiten. Ziehen, wischen, entdecken.").
- Home page tiles: full-width and two-column tiles with 12px gaps, alternating light/dark (`.theme-dark`), text at the top and a full-bleed image below.
- Pill buttons: filled (`.button`) and outlined (`.button--secondary`).
- Breakpoints: 1068px and 734px (plus 834px for the nav); everything scrolls normally, no `overflow: hidden` on `body`.
- Elements with `.reveal` fade/slide in on scroll; disabled with `prefers-reduced-motion`.
- Gallery: click/touch-and-drag horizontal track with parallax (`object-position` animated alongside the track `transform`, 1200ms `animate()` with `fill: "forwards"`), plus horizontal scrolling (trackpad swipe, tilt wheel, Shift + wheel), keyboard (arrows, Home/End) and prev/next buttons. This interaction is the signature element of the site — keep it working when refactoring.

## Known issues / open points

- All copy, project titles, contact data and images are placeholders (see "Project").
- Project tiles and gallery items are not clickable yet — there are no detail views.
- Alt texts say "Platzhalterbild …"; replace with descriptions of the real work.
- Images are JPEG only; no WebP/AVIF or `srcset` yet.
- Nav/footer markup is duplicated across pages (see "File layout").

## Legal requirements (Germany)

A German business/portfolio site needs an **Impressum** (§ 5 DDG) and a **Datenschutzerklärung** (GDPR), both reachable from every page. `impressum.html` and `datenschutz.html` exist as structured placeholders (bracketed fields, yellow "Entwurf" notice, `noindex`) and are linked from every footer. They must be filled in and legally checked by the user before the site goes live. Don't write legal texts as if final.

Also: avoid embedding third-party resources that send visitor data (Google Fonts via CDN, external analytics, embeds) without telling the user — self-host fonts instead. If that changes, update section 4 of `datenschutz.html`.

## Roadmap / ideas for further development

Not decided yet — confirm with the user before starting larger items:

- Portfolio detail views (lightbox or project pages with title, client, year, description); make tiles/gallery items link to them.
- Real content: biography, contact, projects, optimized images (WebP/AVIF, `srcset`).
- Open Graph tags per page.
- `mailto:` / `tel:` links once real contact data exists.
- Possibly a small build step or includes for the shared nav/footer (ask first — currently no tooling).

## Conventions

- Keep it dependency-free and readable; small, focused files.
- Use semantic HTML (`header`, `nav`, `main`, `footer`), relative paths, 4-space indentation, BEM-style class names (`block__element--modifier`); no IDs for styling.
- Test changes in a browser at desktop and phone widths (≈375px) before calling them done.
- Accessibility (target WCAG 2.2 AA, checked in `tests/e2e/test_accessibility.py`): new colours need ≥4.5:1 for text and ≥3:1 for control borders/focus rings in **both** themes; links inside running text (`p a`) stay underlined; visible focus via `outline` (never `outline: none` + box-shadow; white ring inside the dark nav); lists styled without bullets get `role="list"`; an `aria-label` must start with the button's visible text; the open mobile menu makes the rest of the page `inert`; use `aria-disabled` rather than `disabled` for buttons that can be focused when they switch off.
- Don't commit unless the user asks.

## Git workflow (feature branching)

- `main` — release versions only. `development` — integration branch and the repository's default branch.
- **Never commit directly to `main` or `development`.** All work happens on a feature branch created from an up-to-date `development` (e.g. `feature/<short-name>`, `fix/<short-name>`).
- Feature branches merge into `development` (via pull request); `development` merges into `main` for a release.
- Pull requests for features target `development`, not `main`.
- If uncommitted work is found on `main` or `development`, move it to a feature branch before committing.
- CI: `.github/workflows/tests.yml` installs with `uv sync --frozen`, checks `uv lock --check`, runs `ruff check`, `ruff format --check`, installs Chromium and runs `pytest` incl. browser tests (job/check name `tests`, Python 3.11) on pull requests into and pushes to `development`/`main`. The GitHub rulesets for both branches require the `tests` check, so PRs can't be merged with failing tests. Run `uv run pytest` and ruff before pushing; don't rename the job without updating the rulesets.
