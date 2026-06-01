"""Browser Tools — Web browsing and interaction"""
import subprocess
import json
import time
import re
from dataclasses import dataclass, field
from typing import Optional
from urllib.parse import urlparse


@dataclass
class BrowserResult:
    success: bool
    data: dict = field(default_factory=dict)
    error: str = ""
    url: str = ""
    action: str = ""
    duration_ms: float = 0.0

    def to_dict(self) -> dict:
        return {
            "success": self.success,
            "data": self.data,
            "error": self.error,
            "url": self.url,
            "action": self.action,
            "duration_ms": self.duration_ms,
        }


class BrowserTools:
    """Web browsing and page interaction tools."""

    BLOCKED_HOSTS = {
        "localhost", "127.0.0.1", "::1", "0.0.0.0",
        "169.254.169.254",  # AWS metadata
        "metadata.google.internal",  # GCP metadata
    }

    def __init__(self, timeout: int = 30):
        self.timeout = timeout
        self._history: list[dict] = []

    def open_url(self, url: str, wait_for: str = "",
                 timeout: int = None) -> BrowserResult:
        start = time.time()

        parsed = urlparse(url)
        if parsed.hostname in self.BLOCKED_HOSTS:
            return BrowserResult(
                success=False,
                error=f"Blocked host: {parsed.hostname}",
                url=url,
                action="open",
            )

        timeout = timeout or self.timeout

        try:
            result = subprocess.run(
                ["curl", "-sL", "-m", str(timeout), "-o", "/dev/null",
                 "-w", "%{http_code}|%{url_effective}|%{size_download}|%{time_total}",
                 url],
                capture_output=True,
                text=True,
                timeout=timeout + 5,
            )

            duration = (time.time() - start) * 1000

            if result.returncode == 0 and "|" in result.stdout:
                parts = result.stdout.split("|")
                return BrowserResult(
                    success=True,
                    data={
                        "status_code": int(parts[0]) if parts[0].isdigit() else 0,
                        "final_url": parts[1] if len(parts) > 1 else url,
                        "size_bytes": int(parts[2]) if len(parts) > 2 and parts[2].isdigit() else 0,
                        "load_time_sec": float(parts[3]) if len(parts) > 3 else 0,
                    },
                    url=url,
                    action="open",
                    duration_ms=duration,
                )

            return BrowserResult(
                success=False,
                error=f"Failed to load: {result.stderr}",
                url=url,
                action="open",
                duration_ms=duration,
            )
        except Exception as e:
            return BrowserResult(
                success=False,
                error=str(e),
                url=url,
                action="open",
                duration_ms=(time.time() - start) * 1000,
            )

    def fetch_content(self, url: str, max_bytes: int = 1048576) -> BrowserResult:
        start = time.time()

        parsed = urlparse(url)
        if parsed.hostname in self.BLOCKED_HOSTS:
            return BrowserResult(
                success=False,
                error=f"Blocked host: {parsed.hostname}",
                url=url,
                action="fetch",
            )

        try:
            result = subprocess.run(
                ["curl", "-sL", "-m", str(self.timeout),
                 "--max-filesize", str(max_bytes), url],
                capture_output=True,
                text=True,
                timeout=self.timeout + 5,
            )

            duration = (time.time() - start) * 1000

            if result.returncode == 0:
                content = result.stdout[:max_bytes]
                text_only = re.sub(r"<[^>]+>", " ", content)
                text_only = re.sub(r"\s+", " ", text_only).strip()

                return BrowserResult(
                    success=True,
                    data={
                        "html": content[:10000],
                        "text": text_only[:5000],
                        "size_bytes": len(content.encode()),
                    },
                    url=url,
                    action="fetch",
                    duration_ms=duration,
                )

            return BrowserResult(
                success=False,
                error=f"Fetch failed: {result.stderr}",
                url=url,
                action="fetch",
                duration_ms=duration,
            )
        except Exception as e:
            return BrowserResult(
                success=False,
                error=str(e),
                url=url,
                action="fetch",
                duration_ms=(time.time() - start) * 1000,
            )

    def screenshot(self, url: str, output_path: str = "/tmp/screenshot.png",
                   width: int = 1280, height: int = 720) -> BrowserResult:
        start = time.time()

        try:
            result = subprocess.run(
                ["google-chrome", "--headless", "--disable-gpu",
                 f"--window-size={width},{height}",
                 f"--screenshot={output_path}",
                 "--hide-scrollbars", url],
                capture_output=True,
                text=True,
                timeout=self.timeout + 10,
            )

            duration = (time.time() - start) * 1000

            import os
            if os.path.exists(output_path):
                size = os.path.getsize(output_path)
                return BrowserResult(
                    success=True,
                    data={"path": output_path, "size_bytes": size},
                    url=url,
                    action="screenshot",
                    duration_ms=duration,
                )

            return BrowserResult(
                success=False,
                error="Screenshot not created",
                url=url,
                action="screenshot",
                duration_ms=duration,
            )
        except FileNotFoundError:
            return BrowserResult(
                success=False,
                error="Chrome/Chromium not installed",
                url=url,
                action="screenshot",
                duration_ms=(time.time() - start) * 1000,
            )
        except Exception as e:
            return BrowserResult(
                success=False,
                error=str(e),
                url=url,
                action="screenshot",
                duration_ms=(time.time() - start) * 1000,
            )

    def search(self, query: str, engine: str = "google") -> BrowserResult:
        engines = {
            "google": f"https://www.google.com/search?q={query.replace(' ', '+')}",
            "duckduckgo": f"https://duckduckgo.com/?q={query.replace(' ', '+')}",
            "bing": f"https://www.bing.com/search?q={query.replace(' ', '+')}",
        }
        url = engines.get(engine, engines["google"])
        return self.fetch_content(url)

    def get_history(self) -> list[dict]:
        return list(self._history)
