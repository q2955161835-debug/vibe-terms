from __future__ import annotations

import hashlib
import subprocess
import sys
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SITE = ROOT / "site"
DIST = ROOT / "dist"
ARCHIVE = DIST / "vibe-terms-public-site.zip"
CHECKSUM = DIST / "vibe-terms-public-site.zip.sha256"


def build_site() -> None:
    subprocess.run(
        [sys.executable, str(ROOT / "scripts" / "build_static_site.py")],
        cwd=ROOT,
        check=True,
        text=True,
    )


def package_site() -> Path:
    build_site()
    DIST.mkdir(parents=True, exist_ok=True)
    ARCHIVE.unlink(missing_ok=True)

    with zipfile.ZipFile(
        ARCHIVE,
        mode="w",
        compression=zipfile.ZIP_DEFLATED,
        compresslevel=9,
    ) as package:
        for path in sorted(SITE.rglob("*")):
            if path.is_file():
                package.write(path, path.relative_to(SITE).as_posix())

    digest = hashlib.sha256(ARCHIVE.read_bytes()).hexdigest()
    CHECKSUM.write_text(f"{digest}  {ARCHIVE.name}\n", encoding="utf-8")
    return ARCHIVE


if __name__ == "__main__":
    archive = package_site()
    print(f"packaged {archive.relative_to(ROOT)}")
