# CLAUDE.md

Guidance for Claude Code when working in this repository.

## Project

Portfolio homepage for **Jeanette Ulbricht**, a media designer (Mediengestalterin). The site presents her work (portfolio), a short biography and contact details. Audience: potential clients and employers, mostly German-speaking.

The current code is an early **draft / prototype** (v1.0). Treat it as a starting point, not as an architecture to preserve. Improving structure is welcome as long as the visual identity (see below) is kept unless the user asks otherwise.

- Site language: **German** (navigation, headings, copy). Code, comments and commit messages: English.
- Author/maintainer: Philipp Schöneberg (`<meta name="author">`).
- Placeholder content everywhere: Lorem-ipsum biography, masked e-mail/phone, stock example images. Never invent real contact data, biography facts or project descriptions; leave clear placeholders and ask.

## Tech stack

Plain static site — **HTML, CSS, vanilla JavaScript**. No build step, no package manager, no framework, no tests.

Run locally by opening `index.html` in a browser, or serve the folder:

```bash
python3 -m http.server 8000
```

Don't introduce a framework, bundler or npm dependencies without asking the user first. If tooling is added later, update this file.

## File layout

| File | Purpose |
| --- | --- |
| `index.html` / `index.css` / `index.js` | Portfolio page (landing page): horizontal draggable image track |
| `biography.html` / `biography.css` | Biography: profile picture + text |
| `contact.html` / `contact.css` | Contact details + legal disclaimer ("Hinweis") footer |
| `sizeFitter.js` | Swaps element IDs (`main0`↔`main1`, `footer0`↔`footer1`) below 800px width for a mobile layout; used by biography and contact |
| `images/exampleSet0/` | Profile picture placeholder + `favicon.ico` |
| `images/exampleSet1/` | Portfolio placeholder images (`image0–7.jpg`) |

Every page repeats the same `<head>`, header (`#top`, `#logo-name`, `#navigation`) and the same base CSS (body, header, nav). Changes to shared parts must be applied to **all three pages** (or, better, extracted — see roadmap).

## Visual identity (current design)

- Black background, white text, grey (`grey`) for hover states and secondary text.
- Font: Arial / Helvetica / sans-serif.
- Centered name as logo (32px bold), simple text navigation below: Biografie · Portfolio · Kontakt.
- Full-viewport pages with `overflow: hidden`; content absolutely centered.
- Portfolio interaction: click-and-drag horizontal image track with parallax (`object-position` animated alongside the track `transform`, 1200ms `animate()` with `fill: "forwards"`). This interaction is the signature element of the site — keep it working when refactoring.

## Known issues in the draft

Fix these when touching the relevant code (or when asked):

1. **`sizeFitter.js` only runs on `resize`**, not on initial load — a page opened on a phone starts with the desktop layout.
2. **`sizeFitter.js` crashes on `biography.html`**: there is no `#footer0`, so `footer.id = ...` throws on a null element.
3. The mobile layout is done by swapping IDs in JS. Prefer CSS media queries (and classes instead of IDs for styling).
4. `index.js` leaks globals (`maxDelta`, `nextPercentage` declared without `const`/`let` via comma lines that actually end in `;`).
5. The image track only handles mouse events — **no touch support**, so the portfolio is not usable on phones/tablets. Use Pointer Events.
6. The portfolio page has no mobile layout at all and `overflow: hidden` on `body` can cut off content on small screens (e.g. the long contact footer).
7. Duplicate `<meta charset>` in every page; `<html>` lacks `lang="de"`; `</BR>` is invalid markup.
8. Shared CSS is copy-pasted into three files.
9. Alt texts are generic (`Image0`, `Profile picture`) — should describe the work.
10. No keyboard access for the image track; no visible focus styles.

## Legal requirements (Germany)

A German business/portfolio site needs an **Impressum** (§ 5 DDG) and a **Datenschutzerklärung** (GDPR), both reachable from every page (usually footer links). Neither exists yet. The "Hinweis" disclaimer on the contact page is an outdated boilerplate link disclaimer with no legal effect; it can be replaced by the Impressum. Don't write legal texts as if final — produce structured placeholders and tell the user they need to be checked/filled in by them.

Also: avoid embedding third-party resources that send visitor data (Google Fonts via CDN, external analytics, embeds) without telling the user — self-host fonts instead.

## Roadmap / ideas for further development

Not decided yet — confirm with the user before starting larger items:

- Extract shared CSS into one stylesheet (e.g. `css/base.css`) plus small page-specific files; use CSS custom properties for colours/spacing.
- Replace `sizeFitter.js` with media queries; make all pages responsive and scrollable where needed.
- Pointer/touch + keyboard support for the image track; respect `prefers-reduced-motion`.
- Portfolio detail views (lightbox or project pages with title, client, year, description).
- Real content: biography, contact, projects, optimized images (WebP/AVIF, `srcset`, `loading="lazy"`, `width`/`height` attributes).
- Impressum and Datenschutz pages; footer with links on every page.
- SEO basics: unique `<title>` and `<meta name="description">` per page, Open Graph tags, `lang="de"`.
- Possibly a `mailto:` link or contact form (a form needs a backend/service — ask first).

## Conventions

- Keep it dependency-free and readable; small, focused files.
- Use semantic HTML (`header`, `nav`, `main`, `footer`), relative paths, 4-space indentation (some lines currently use tabs — normalize when editing).
- Test changes in a browser at desktop and phone widths (≈375px) before calling them done.
- Don't commit unless the user asks.

## Git workflow (feature branching)

- `main` — release versions only. `development` — integration branch and the repository's default branch.
- **Never commit directly to `main` or `development`.** All work happens on a feature branch created from an up-to-date `development` (e.g. `feature/<short-name>`, `fix/<short-name>`).
- Feature branches merge into `development` (via pull request); `development` merges into `main` for a release.
- Pull requests for features target `development`, not `main`.
- If uncommitted work is found on `main` or `development`, move it to a feature branch before committing.
