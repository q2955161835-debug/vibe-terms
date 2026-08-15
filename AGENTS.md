# AGENTS.md

## Current milestone

Ship the anonymous static Vibe Terms prototype. Authentication, Supabase, user
accounts, cloud synchronization, payments, reminders, and analytics are
explicitly deferred.

## Sources of truth

- `content/` contains canonical terminology, localization, taxonomy, and the
  prototype learning path.
- English is canonical. Every translation keeps `source_content_version`
  aligned with its term metadata.
- `web/` contains browser runtime and visual source files.
- `site/` and `dist/` are generated and ignored. Never edit or commit them.

## Required commands

```bash
python3 -m pip install -r requirements-dev.txt
./scripts/verify_public_site.sh
```

Set `RUN_HTTP_E2E=1` for the true localhost navigation suite. Set
`PLAYWRIGHT_CHROMIUM_EXECUTABLE=/path/to/chromium` when using an existing
browser binary instead of Playwright's downloaded Chromium.

## Engineering rules

1. Add or update a failing test before changing observable behavior.
2. Keep term and category pages useful without JavaScript.
3. Preserve exactly these locale routes: `en`, `zh-cn`, `zh-tw`, `ja`, `ko`,
   `de`, `ru`, and `hi`.
4. Store structured guest learning data in IndexedDB, with localStorage only as
   an explicit fallback and for small preferences.
5. Do not add login-looking UI while the account system is deferred.
6. Keep English canonical names visible on localized term pages.
7. Do not commit secrets, tokens, `.env` files, generated output, or browser
   profiles.
8. Keep the static archive host-independent. Codex Sites is a deployment target,
   not a runtime dependency.
