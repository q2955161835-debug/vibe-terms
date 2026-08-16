# Vibe Terms

An open multilingual Vibe Coding terminology dictionary built for people who are
starting from zero.

This milestone is a **no login public site**. Every public page is ordinary
static HTML, CSS, and JavaScript. Search, theme selection, and the daily learning
flow work without an account; guest progress is stored locally in the browser.
There is no user database, OAuth flow, or cloud synchronization in this build.

## Current static platform

- 7 locales: English, Simplified Chinese, Traditional Chinese, Japanese, Korean, German, and Russian
- 500 canonical terms across 12 knowledge domains and 42 second-level topics
- knowledge-map and three chaptered project-path navigation systems
- dense localized term pages with examples, exercises, sources, aliases, and keyboard search
- light, dark, and system themes
- configurable daily new-term count from 1 to 30
- inline and standalone practice with scheduled local review
- versioned IndexedDB storage with a localStorage fallback, export, and clear controls
- static SEO metadata, language alternates, sitemap support, manifest, and a 404 page

English content is canonical and published. Localizations that have not been
human-reviewed remain visibly marked `draft` and are emitted with `noindex`;
the site never presents draft translation status as editorial approval.

## Requirements

- Python 3.11 or newer
- Node.js 22.13 or newer for the JavaScript tests and Codex Sites build

## Build locally

```bash
python3 -m venv .venv
. .venv/bin/activate
pip install -r requirements.txt
python3 scripts/build_static_site.py
python3 -m http.server 4173 --directory site
```

Open `http://localhost:4173/`.

The generated output lives in `site/` and is intentionally ignored by Git.

## Production build

Set `SITE_URL` to the final public origin so canonical, Open Graph, robots, and
sitemap URLs are production-ready. Set `GITHUB_URL` only after the source
repository is public.

```bash
SITE_URL=https://terms.example.com \
GITHUB_URL=https://github.com/example/vibe-terms \
python3 scripts/build_static_site.py
```

Create a direct-hosting archive with:

```bash
python3 scripts/package_site.py
```

This writes `dist/vibe-terms-public-site.zip` plus a SHA-256 checksum. The ZIP
opens at the hosting root rather than nesting everything inside a `site/` folder.

Deploy the contents of `site/` at the hostname root. A generic static host can
use:

```text
Install command: pip install -r requirements.txt
Build command:   python3 scripts/build_static_site.py
Output directory: site
```

For this repository's GitHub Pages project site, build with the project prefix:

```bash
BASE_PATH=/vibe-terms \
SITE_URL=https://q2955161835-debug.github.io/vibe-terms \
GITHUB_URL=https://github.com/q2955161835-debug/vibe-terms \
python3 scripts/build_static_site.py
```

`.github/workflows/deploy-pages.yml` publishes the same generated `site/`
artifact after an accepted change reaches `main`.

Codex Sites uses the tracked adapter in `app/`, `worker/`, `vite.config.ts`, and
`.openai/hosting.json`. It preserves the generated static pages and packages
them into the Worker-compatible build expected by Sites:

```bash
npm ci
npm run build
```

More detail is in [`docs/deployment.md`](docs/deployment.md).

## Test

```bash
pip install -r requirements-dev.txt
./scripts/verify_public_site.sh
```

The default command runs content contracts, packaging tests, JavaScript unit
tests, and a Chromium render harness that does not require localhost navigation.
Run the full HTTP navigation suite in an unrestricted browser environment with:

```bash
python3 -m playwright install chromium
RUN_HTTP_E2E=1 ./scripts/verify_public_site.sh
```

Set `PLAYWRIGHT_CHROMIUM_EXECUTABLE=/path/to/chromium` when using an existing
Chromium installation.

## Repository map

```text
content/   canonical terminology, localization, taxonomy, and project paths
scripts/   modular static generator, packaging, and verification commands
web/       browser runtime, styles, and logo
app/       minimal vinext shell used only for Codex Sites packaging
worker/    static-route adapter for the Sites runtime
site/      generated deployable output, not committed
tests/     content, URL, static-contract, JavaScript, rendering, and browser tests
docs/      product specifications, plans, and deployment notes
```

## Licenses

- Software code: Apache-2.0, see [`LICENSE`](LICENSE)
- Terminology and editorial content: CC BY-SA 4.0, see [`LICENSE-CONTENT`](LICENSE-CONTENT)
