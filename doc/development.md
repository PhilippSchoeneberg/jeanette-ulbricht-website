# Development

## Setup

Requires [uv](https://docs.astral.sh/uv/) (`brew install uv`) and Python 3.11 or newer (uv can
install it).

```bash
uv sync                                # creates .venv with all dependencies from uv.lock
uv run playwright install chromium     # browser for the browser tests (once, ~150 MB)
cp .env.example .env
```

For local development, leave `SMTP_HOST` in `.env` empty: contact form messages are then printed
to the server console instead of being sent. To test real sending, fill in the SMTP settings
(see `.env.example`).

## Run

From the repository root:

```bash
uv run uvicorn src.backend.main:app --reload
```

Open http://127.0.0.1:8000. The API docs are at http://127.0.0.1:8000/api/docs.

The frontend has no build step: edit files in `src/frontend` and reload the page. Without the
backend (e.g. `python3 -m http.server 8000 --directory src/frontend`) all pages work except
sending the contact form.

## Dependencies

Dependencies are declared in `pyproject.toml` (minimum versions) and pinned in `uv.lock` (exact
versions); commit both. CI fails if `uv.lock` doesn't match `pyproject.toml`.

```bash
uv add <package>              # runtime dependency
uv add --dev <package>        # test/dev dependency
uv lock --upgrade             # update everything within the declared ranges
```

## Tests

The tests run the real FastAPI app with a fake mailer, so they need no mail server and no `.env`.

- `tests/test_*.py`: API and translation tests (fast, no browser).
- `tests/e2e/`: browser tests with [Playwright](https://playwright.dev/python/)
  (`pytest-playwright`). They start the app with uvicorn on a free local port and drive headless
  Chromium through the main flows: gallery (drag, keyboard, prev/next buttons, parallax), theme
  toggle, language switch, mobile menu at 375px and the contact form (field errors, successful
  send, rate limit, mail error). Each test gets a fresh browser (empty `localStorage`), German,
  light mode and reduced motion, so animations finish instantly.

```bash
uv run pytest                          # everything
uv run pytest -m "not e2e"             # without the browser tests
uv run pytest tests/e2e --headed       # watch the browser
uv run pytest tests/e2e --headed --slowmo 500
```

The browser tests need Chromium (`uv run playwright install chromium`); without it they fail
with "Executable doesn't exist". On failure, `--tracing retain-on-failure` saves a trace to
`test-results/` that `uv run playwright show-trace <file>` opens.

## Linting and formatting

Python code is checked with [ruff](https://docs.astral.sh/ruff/) (settings under `[tool.ruff]` in
`pyproject.toml`):

```bash
uv run ruff check .          # lint (add --fix to fix what can be fixed automatically)
uv run ruff format .         # format
```

## Check before committing

Run the tests, including the browser tests, and ruff (`uv run ruff check .` and
`uv run ruff format --check .`). The tests cover the main flows, but not the look: check changes
in a browser at desktop width and at phone width (about 375px), in light and dark mode, on every
page you touched. Add or adjust a test in `tests/e2e` when you change gallery, navigation, theme,
language or contact form behaviour.

## Content

All texts, contact data and images are placeholders.

Texts are German in the HTML and in `src/frontend/locales/de.json`, English in `en.json`. When
adding or changing a text: give the element a `data-i18n` key (or `data-i18n-<attribute>` for
attributes like `alt`), put the same German text into `de.json` and the English one into
`en.json`, then run the tests: they report missing, unused or mismatched keys.
 Don't invent real content: biography,
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

## Continuous integration

`.github/workflows/tests.yml` installs the locked dependencies with uv, checks that `uv.lock` is up
to date, runs `ruff check` and `ruff format --check`, installs Chromium and runs `pytest` (API and
browser tests) on GitHub Actions (Python 3.11, the oldest supported version):

- on every pull request into `development` or `main`,
- after every merge (push) into `development` or `main`,
- manually from the repository's **Actions** tab.

The job is called `tests`. The rulesets for `development` and `main` (repository **Settings →
Rules → Rulesets**) require it as a status check, so a pull request can only be merged once linting and
tests pass (both run in the `tests` job). Together with the other ruleset rules, `development` and `main` can only change
through pull requests, can't be force-pushed and can't be deleted.

To set the required check up again (e.g. for a new protected branch): open the ruleset, enable
**Require status checks to pass**, add the check `tests` (source: GitHub Actions) and save. The
check can only be selected after the workflow has run at least once. If the job is ever renamed,
update the rulesets too, otherwise pull requests wait forever for a check that never reports.

