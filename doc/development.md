# Development

## Run

Requires only Python 3 (for a local web server). From the repository root:

```bash
python3 -m http.server 8000 --directory src/frontend
```

Open http://127.0.0.1:8000. There is no build step: edit files in `src/frontend` and reload the
page. Opening the HTML files directly also works, but a server is closer to the real hosting.

## Check before committing

There are no automated tests. Check changes in a browser at desktop width and at phone width
(about 375px), on every page you touched. For the portfolio page, also check that the gallery
can be dragged, scrolled sideways and moved with the keyboard.

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
