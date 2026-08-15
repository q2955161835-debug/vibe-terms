from __future__ import annotations

import subprocess
import sys
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ARCHIVE = ROOT / "dist" / "vibe-terms-public-site.zip"


def test_static_archive_is_ready_for_direct_hosting() -> None:
    subprocess.run(
        [sys.executable, "scripts/package_site.py"],
        cwd=ROOT,
        check=True,
        text=True,
    )

    assert ARCHIVE.is_file()
    with zipfile.ZipFile(ARCHIVE) as package:
        names = set(package.namelist())

    required = {
        "index.html",
        "404.html",
        "manifest.webmanifest",
        "assets/app.js",
        "assets/core.js",
        "en/index.html",
        "zh-cn/index.html",
        "zh-tw/index.html",
        "ja/index.html",
        "ko/index.html",
        "de/index.html",
        "ru/index.html",
        "hi/index.html",
    }
    assert required <= names
    assert not any(name.startswith("site/") for name in names)
    assert not any("__pycache__" in name for name in names)
    assert not any(name.endswith((".py", ".yaml", ".env")) for name in names)
