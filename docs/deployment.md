# Static Deployment

Vibe Terms currently builds as a host-independent static site. No login service,
server runtime, or user database is required. Guest learning data stays in the
visitor's browser.

## Build inputs and output

- Build command: `python3 scripts/build_static_site.py`
- Output directory: `site/`
- Required environment variable for production SEO: `SITE_URL`
- Optional source link: `GITHUB_URL`

Example production build:

```bash
SITE_URL=https://terms.example.com \
GITHUB_URL=https://github.com/example/vibe-terms \
python3 scripts/build_static_site.py
```

`SITE_URL` must be the public origin without a trailing slash. Setting it creates
absolute canonical URLs, Open Graph URLs, and sitemap entries. When it is absent,
the output remains locally testable but the sitemap intentionally contains no
production URLs.

## Direct-hosting archive

```bash
python3 scripts/package_site.py
```

The command rebuilds the site, creates `dist/vibe-terms-public-site.zip`, and
writes `dist/vibe-terms-public-site.zip.sha256`. Files are stored at the archive
root so the ZIP can be extracted directly into a static host's publish directory.

## Static-host configuration

Use this configuration on any service that accepts a build command and output
directory:

```text
Install: pip install -r requirements.txt
Build:   python3 scripts/build_static_site.py
Output:  site
```

The host must serve directory indexes, preserve `404.html`, and publish files
from the root of `site/`. No rewrite to an application server is needed.

## Codex Sites handoff

The repository includes a thin vinext/Worker adapter for Codex Sites. It does
not replace the static generator: `npm run build` first regenerates `site/`,
copies it into the ignored Sites public-asset directory, and then emits the
Worker-compatible `dist/server/index.js` bundle.

```bash
npm ci
npm run build
```

The tracked `.openai/hosting.json` stores only the Sites project binding and
optional logical storage bindings. Runtime values remain managed by Sites. Set
`SITE_URL` after the production hostname is known and rebuild so canonical,
Open Graph, and sitemap URLs use the deployed origin. `GITHUB_URL` can remain
unset until the source repository is public; the footer then omits the link.

## Verification before release

```bash
./scripts/verify_public_site.sh
```

The default verification includes a policy-independent Chromium render harness.
Before a public release, also run the true HTTP navigation suite in an
environment where Chromium may open localhost:

```bash
RUN_HTTP_E2E=1 ./scripts/verify_public_site.sh
```

To use a system Chromium binary:

```bash
PLAYWRIGHT_CHROMIUM_EXECUTABLE=/usr/bin/chromium \
RUN_HTTP_E2E=1 ./scripts/verify_public_site.sh
```
