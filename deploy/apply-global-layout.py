#!/usr/bin/env python3
"""Apply shared site-wide HTML includes to every staged public page."""

from __future__ import annotations

import re
import sys
from pathlib import Path


CONTAINER_ID = "GTM-T9SDSZMJ"
LAYOUT_DIR = Path(__file__).resolve().parent / "global-layout"


def insert_after_opening_tag(html: str, tag: str, snippet: str, page: Path) -> str:
    matches = list(re.finditer(rf"<{tag}\b[^>]*>", html, flags=re.IGNORECASE))
    if len(matches) != 1:
        raise ValueError(
            f"{page}: expected exactly one <{tag}> element, found {len(matches)}"
        )

    match = matches[0]
    line_start = html.rfind("\n", 0, match.start()) + 1
    prefix = html[line_start : match.start()]
    parent_indent = prefix if not prefix.strip() else ""
    child_indent = f"{parent_indent}  "
    rendered = "\n".join(
        f"{child_indent}{line}" if line else "" for line in snippet.splitlines()
    )

    remainder = html[match.end() :]
    if remainder.startswith("\r\n"):
        remainder = remainder[2:]
    elif remainder.startswith("\n"):
        remainder = remainder[1:]

    return f"{html[:match.end()]}\n{rendered}\n{remainder}"


def apply_global_layout(page: Path, head: str, body: str) -> None:
    html = page.read_text(encoding="utf-8")
    if CONTAINER_ID in html:
        raise ValueError(
            f"{page}: contains a page-local {CONTAINER_ID}; use the shared layout"
        )

    html = insert_after_opening_tag(html, "head", head, page)
    html = insert_after_opening_tag(html, "body", body, page)
    page.write_text(html, encoding="utf-8")


def main() -> int:
    if len(sys.argv) != 2:
        print(f"usage: {Path(sys.argv[0]).name} STAGING_ROOT", file=sys.stderr)
        return 2

    staging_root = Path(sys.argv[1]).resolve()
    if not staging_root.is_dir():
        print(f"staging root is not a directory: {staging_root}", file=sys.stderr)
        return 2

    head = (LAYOUT_DIR / "gtm-head.html").read_text(encoding="utf-8").strip()
    body = (LAYOUT_DIR / "gtm-body.html").read_text(encoding="utf-8").strip()
    pages = sorted(staging_root.rglob("*.html"))
    if not pages:
        print(f"no HTML pages found under {staging_root}", file=sys.stderr)
        return 1

    try:
        for page in pages:
            apply_global_layout(page, head, body)
    except (OSError, UnicodeError, ValueError) as error:
        print(error, file=sys.stderr)
        return 1

    print(f"==> applied global layout to {len(pages)} HTML page(s)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
