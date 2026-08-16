from __future__ import annotations

import os
import subprocess
import sys
import threading
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlsplit

import pytest

ROOT = Path(__file__).resolve().parents[1]
SITE = ROOT / "site"

@pytest.fixture(scope="session", autouse=True)
def build_site() -> Path:
    subprocess.run(
        [sys.executable, "scripts/build_static_site.py"],
        cwd=ROOT,
        check=True,
        text=True,
    )
    return SITE


@pytest.fixture(scope="session")
def site_url(build_site: Path) -> str:
    base_path = os.environ.get("BASE_PATH", "").rstrip("/")

    class BasePathHandler(SimpleHTTPRequestHandler):
        def __init__(self, *args, **kwargs):
            super().__init__(*args, directory=str(build_site), **kwargs)

        def translate_path(self, path: str) -> str:
            request_path = urlsplit(path).path
            if base_path and request_path == base_path:
                request_path = "/"
            elif base_path and request_path.startswith(f"{base_path}/"):
                request_path = request_path[len(base_path):]
            return super().translate_path(request_path)

        def log_message(self, format: str, *args) -> None:
            pass

    server = ThreadingHTTPServer(("127.0.0.1", 0), BasePathHandler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    url = f"http://127.0.0.1:{server.server_port}{base_path}"

    try:
        yield url
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=5)
