# Deployment

The site is static: publishing it means uploading the contents of `src/frontend` to the web root
of any web host. `index.html` must end up at the root. No server-side code or build step is
needed.

Hosting has not been chosen yet.

## Before going live

- Replace all placeholder content (texts, contact data, images, alt texts).
- Fill in `impressum.html` and `datenschutz.html`, have them checked legally, then remove the
  yellow "Entwurf" notice and the `noindex` meta tag from both pages.
- Describe the chosen host and its server logs in section 2 of the Datenschutzerklärung.
- Release from `main` only (see [Development](development.md#git-workflow)).
