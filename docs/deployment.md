# Static Deployment

Vibe Terms currently builds as a host-independent static site. No login service,
server runtime, or user database is required. Guest learning data stays in the
visitor's browser.

## Build inputs and output

- Build command: `python3 scripts/build_static_site.py`
- Output directory: `site/`
- Required environment variable for production SEO: `SITE_URL`
- Optional project-site prefix: `BASE_PATH` (empty at a root host)
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

## GitHub Pages project site

The public repository is deployed at
`https://q2955161835-debug.github.io/vibe-terms/`. GitHub Pages serves it below
the repository name, so every internal page and asset URL must be generated with
`BASE_PATH=/vibe-terms`:

```bash
BASE_PATH=/vibe-terms \
SITE_URL=https://q2955161835-debug.github.io/vibe-terms \
GITHUB_URL=https://github.com/q2955161835-debug/vibe-terms \
python3 scripts/build_static_site.py
```

The `Deploy GitHub Pages` workflow builds `site/`, uploads it as a Pages
artifact, and deploys only from `main`. A successful workflow is not the final
gate: read back the live root, one locale, one term, the knowledge map, a path
chapter, practice, `llms.txt`, `og.png`, and an explainer asset after deployment.

The root landing page owns the site-wide Open Graph/X image metadata; ordinary
term pages retain their own text metadata and do not pretend that the landing
card is a per-term illustration. Both `og.png` and discovery files must use a
single `/vibe-terms` prefix in the Pages build.

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

Sites deployment must use the same committed source revision that was pushed to
GitHub. Package the completed `npm run build` output with the Sites plugin,
save a version bound to that Git SHA, deploy it privately, poll to `succeeded`,
then read back the returned deployment URL. Never retain a temporary Sites
source credential in Git configuration, remotes, logs, or documentation.

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
