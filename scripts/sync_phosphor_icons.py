"""Copy the audited Phosphor SVG subset from the locked npm dependency."""

from __future__ import annotations

import argparse
import shutil
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
ICON_NAMES = (
    "arrow-right", "browser", "brackets-curly", "check-circle", "code",
    "database", "file", "folder", "git-branch", "lock", "magnifying-glass",
    "hard-drives", "shield-check", "terminal", "warning-circle",
)
SOURCE_ROOT = ROOT / "node_modules" / "@phosphor-icons" / "core"
SOURCE_ICONS = SOURCE_ROOT / "assets" / "regular"
DESTINATION = ROOT / "web" / "icons"
LICENSE_NAME = "LICENSE.phosphor.txt"


def expected_files() -> dict[Path, Path]:
    sources = {DESTINATION / f"{name}.svg": SOURCE_ICONS / f"{name}.svg" for name in ICON_NAMES}
    sources[DESTINATION / LICENSE_NAME] = SOURCE_ROOT / "LICENSE"
    return sources


def verify_sources(files: dict[Path, Path]) -> list[str]:
    return [f"missing vendor source: {source}" for source in files.values() if not source.is_file()]


def check(files: dict[Path, Path]) -> list[str]:
    errors = verify_sources(files)
    actual = set(DESTINATION.iterdir()) if DESTINATION.is_dir() else set()
    expected = set(files)
    for path in sorted(actual - expected):
        errors.append(f"unexpected icon file: {path.name}")
    for destination, source in files.items():
        if not destination.is_file():
            errors.append(f"missing synced file: {destination.name}")
        elif source.is_file() and destination.read_bytes() != source.read_bytes():
            errors.append(f"outdated synced file: {destination.name}")
    return errors


def sync(files: dict[Path, Path]) -> list[str]:
    errors = verify_sources(files)
    if errors:
        return errors
    DESTINATION.mkdir(parents=True, exist_ok=True)
    expected = set(files)
    for path in DESTINATION.iterdir():
        if path not in expected:
            errors.append(f"unexpected icon file: {path.name}")
    if errors:
        return errors
    for destination, source in files.items():
        shutil.copyfile(source, destination)
    return []


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true", help="verify without writing files")
    args = parser.parse_args()
    files = expected_files()
    errors = check(files) if args.check else sync(files)
    if errors:
        print("\n".join(errors), file=sys.stderr)
        return 1
    print(f"Phosphor icon subset verified: {len(ICON_NAMES)} SVGs plus MIT license.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
