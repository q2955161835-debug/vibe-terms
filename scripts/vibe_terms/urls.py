from __future__ import annotations

from urllib.parse import urlsplit


class UrlBuilder:
    """Build public URLs without coupling generated files to one host."""

    def __init__(self, site_url: str = "", base_path: str = "") -> None:
        site_url = site_url.strip()
        base_path = base_path.strip()
        if base_path and (
            not base_path.startswith("/")
            or base_path.endswith("/")
            or any(character in base_path for character in ("?", "#"))
            or urlsplit(base_path).scheme
            or base_path.startswith("//")
        ):
            raise ValueError(
                "base_path must be empty or an absolute path without a trailing slash"
            )
        if site_url.endswith("/"):
            raise ValueError("site_url must not have a trailing slash")
        if site_url:
            parsed = urlsplit(site_url)
            if parsed.scheme not in {"http", "https"} or not parsed.netloc:
                raise ValueError("site_url must be an absolute HTTP(S) origin or URL")
            if parsed.query or parsed.fragment:
                raise ValueError("site_url must not include a query or fragment")
        self.site_url = site_url
        self.base_path = base_path

    @staticmethod
    def _path(path: str) -> str:
        clean = str(path).strip()
        if not clean.startswith("/"):
            clean = f"/{clean}"
        return clean

    def page(self, path: str = "/") -> str:
        clean = self._path(path)
        if self.base_path and (clean == self.base_path or clean.startswith(f"{self.base_path}/")):
            return clean
        return f"{self.base_path}{clean}" if self.base_path else clean

    def asset(self, path: str) -> str:
        return self.page(path)

    def absolute(self, path: str = "/") -> str:
        public_path = self.page(path)
        if not self.site_url:
            return public_path
        if self.base_path and self.site_url.endswith(self.base_path):
            origin = self.site_url[: -len(self.base_path)]
            return f"{origin}{public_path}"
        return f"{self.site_url}{public_path}"
