#!/usr/bin/env python3
"""Serve the built site locally the way nginx serves it in production.

`python3 -m http.server` gets two things wrong that make the page look broken
when it is not:

  * it answers POST with 501, so the waitlist form always reports a failure;
  * it ignores Range requests, so a browser cannot seek inside a video and
    scrubbing a demo restarts it from the beginning;
  * it answers a bad URL with its own bare 404 rather than the site's page.

Both are answered here, so what you see locally is what the site does live.

    npm run build
    python3 scripts/preview.py

Submitted addresses are printed, not stored.
"""

from __future__ import annotations

import argparse
import json
import re
from functools import partial
from http.server import HTTPStatus, SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
BUILD = ROOT / ".build"
EMAIL = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


RANGE = re.compile(r"^bytes=(\d*)-(\d*)$")


class PreviewHandler(SimpleHTTPRequestHandler):
    def send_head(self):
        """Serve a byte range when one is asked for, as nginx does.

        Video seeking is built on Range: without a 206 the browser cannot jump
        to a timestamp and falls back to replaying from the start.
        """
        header = self.headers.get("Range")
        if not header:
            return super().send_head()

        match = RANGE.match(header.strip())
        path = self.translate_path(self.path)
        if not match or not Path(path).is_file():
            return super().send_head()

        size = Path(path).stat().st_size
        start_text, end_text = match.groups()
        if start_text:
            start = int(start_text)
            end = int(end_text) if end_text else size - 1
        elif end_text:                       # bytes=-500 means the last 500
            start, end = max(0, size - int(end_text)), size - 1
        else:
            return super().send_head()

        end = min(end, size - 1)
        if start > end or start >= size:
            self.send_response(HTTPStatus.REQUESTED_RANGE_NOT_SATISFIABLE)
            self.send_header("Content-Range", f"bytes */{size}")
            self.end_headers()
            return None

        handle = open(path, "rb")
        handle.seek(start)
        self.send_response(HTTPStatus.PARTIAL_CONTENT)
        self.send_header("Content-Type", self.guess_type(path))
        self.send_header("Accept-Ranges", "bytes")
        self.send_header("Content-Range", f"bytes {start}-{end}/{size}")
        self.send_header("Content-Length", str(end - start + 1))
        self.end_headers()
        return _Slice(handle, end - start + 1)

    def end_headers(self) -> None:
        if "Accept-Ranges" not in self._headers_buffer_text():
            self.send_header("Accept-Ranges", "bytes")
        super().end_headers()

    def _headers_buffer_text(self) -> str:
        return b"".join(getattr(self, "_headers_buffer", []) or []).decode("latin-1")

    def send_error(self, code, message=None, explain=None):
        """Serve the site's own 404 page, as nginx's error_page does."""
        page = BUILD / "404.html"
        if code == HTTPStatus.NOT_FOUND and page.is_file():
            body = page.read_bytes()
            self.send_response(HTTPStatus.NOT_FOUND)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            if self.command != "HEAD":
                self.wfile.write(body)
            return
        super().send_error(code, message, explain)

    def do_POST(self) -> None:  # noqa: N802 - name fixed by the base class
        if self.path.split("?")[0] != "/waitlist":
            self.send_error(404, "Not Found")
            return

        length = int(self.headers.get("Content-Length") or 0)
        body = self.rfile.read(length) if length else b"{}"
        try:
            email = (json.loads(body or b"{}").get("email") or "").strip().lower()
        except json.JSONDecodeError:
            self._json({"ok": False, "error": "invalid JSON"}, status=400)
            return

        if not EMAIL.match(email):
            self._json({"ok": False, "error": "invalid email"}, status=400)
            return

        print(f"  waitlist (preview, not stored): {email}")
        self._json({"ok": True, "created": True})

    def _json(self, payload: dict, status: int = 200) -> None:
        encoded = json.dumps(payload).encode()
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(encoded)))
        self.end_headers()
        self.wfile.write(encoded)

    def log_message(self, fmt: str, *args) -> None:
        if "GET" in (args[0] if args else ""):
            return
        super().log_message(fmt, *args)


class _Slice:
    """A read-only window onto an open file, for copyfile() to drain."""

    def __init__(self, handle, length: int) -> None:
        self._handle = handle
        self._left = length

    def read(self, amount: int = -1) -> bytes:
        if self._left <= 0:
            return b""
        if amount is None or amount < 0:
            amount = self._left
        chunk = self._handle.read(min(amount, self._left))
        self._left -= len(chunk)
        return chunk

    def close(self) -> None:
        self._handle.close()


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--port", type=int, default=8899)
    parser.add_argument("--host", default="127.0.0.1")
    arguments = parser.parse_args()

    if not (BUILD / "index.html").is_file():
        raise SystemExit("nothing built yet; run npm run build first")

    handler = partial(PreviewHandler, directory=str(BUILD))
    server = ThreadingHTTPServer((arguments.host, arguments.port), handler)
    print(f"serving {BUILD.relative_to(ROOT)} on http://{arguments.host}:{arguments.port}/")
    print("POST /waitlist is stubbed and Range requests are honoured, so the")
    print("form and video scrubbing behave as they do in production")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nstopped")


if __name__ == "__main__":
    main()
