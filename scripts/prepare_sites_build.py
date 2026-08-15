from __future__ import annotations

import shutil
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
GENERATED_SITE = ROOT / "site"
SITES_PUBLIC = ROOT / "public"


def main() -> None:
    subprocess.run(
        [sys.executable, str(ROOT / "scripts" / "build_static_site.py")],
        cwd=ROOT,
        check=True,
    )
    if SITES_PUBLIC.exists():
        shutil.rmtree(SITES_PUBLIC)
    shutil.copytree(GENERATED_SITE, SITES_PUBLIC)
    print(f"prepared {sum(path.is_file() for path in SITES_PUBLIC.rglob('*'))} Sites assets")


if __name__ == "__main__":
    main()
