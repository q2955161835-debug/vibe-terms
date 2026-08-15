#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

python3 -m py_compile scripts/build_static_site.py scripts/package_site.py
python3 scripts/build_static_site.py
python3 -m pytest -q \
  tests/test_static_site.py \
  tests/test_packaging.py \
  tests/test_render_harness.py
node --check web/core.js
node --check web/app.js
node --test tests/js/core.test.cjs

if [[ "${RUN_HTTP_E2E:-0}" == "1" ]]; then
  python3 -m pytest -q tests/test_browser.py
else
  printf '%s\n' 'HTTP navigation tests skipped. Set RUN_HTTP_E2E=1 in an unrestricted browser environment.' >&2
fi

python3 scripts/package_site.py
echo "Public-site verification passed."
