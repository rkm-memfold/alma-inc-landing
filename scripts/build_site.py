#!/usr/bin/env python3
"""Build every static page through the shared site layout."""

from __future__ import annotations

import argparse
import os
import re
import shutil
import tempfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PAGES = ROOT / "site" / "pages"
LAYOUT = ROOT / "site" / "layout.html"
PUBLIC = ROOT / "public"
GTM_ID = "GTM-T9SDSZMJ"
POSTHOG_TOKEN_FILE = Path("/etc/alma-posthog-project-token")
POSTHOG_TOKEN_PLACEHOLDER = "{{ posthog_project_token }}"


def get_posthog_project_token() -> str:
    token = os.environ.get("POSTHOG_PROJECT_TOKEN", "").strip()
    if not token and POSTHOG_TOKEN_FILE.is_file():
        token = POSTHOG_TOKEN_FILE.read_text(encoding="utf-8").strip()
    if not re.fullmatch(r"phc_[A-Za-z0-9]+", token):
        raise ValueError(
            "POSTHOG_PROJECT_TOKEN must be supplied through the environment "
            f"or {POSTHOG_TOKEN_FILE}"
        )
    return token


def extract(pattern: str, document: str, source: Path, label: str) -> re.Match[str]:
    match = re.search(pattern, document, flags=re.IGNORECASE | re.DOTALL)
    if not match:
        raise ValueError(f"{source.relative_to(ROOT)} is missing its {label}")
    return match


def render_page(source: Path, layout: str, posthog_token: str) -> str:
    document = source.read_text(encoding="utf-8")
    if GTM_ID in document:
        raise ValueError(
            f"{source.relative_to(ROOT)} contains GTM directly; it belongs only in site/layout.html"
        )
    if re.search(r"phc_[A-Za-z0-9]+", document) or "posthog.init" in document:
        raise ValueError(
            f"{source.relative_to(ROOT)} contains PostHog directly; it belongs only in site/layout.html"
        )

    html = extract(r"<html\b(?P<attrs>[^>]*)>", document, source, "<html> element")
    head = extract(r"<head\b[^>]*>(?P<content>.*?)</head>", document, source, "<head> element")
    body = extract(
        r"<body\b(?P<attrs>[^>]*)>(?P<content>.*?)</body>",
        document,
        source,
        "<body> element",
    )

    lang_match = re.search(r"\blang\s*=\s*(['\"])(?P<lang>.*?)\1", html.group("attrs"), re.I)
    lang = lang_match.group("lang") if lang_match else "en"
    body_attributes = body.group("attrs").strip()
    body_attributes = f" {body_attributes}" if body_attributes else ""

    rendered = (
        layout.replace("{{ lang }}", lang)
        .replace("{{ body_attributes }}", body_attributes)
        .replace(POSTHOG_TOKEN_PLACEHOLDER, posthog_token)
        .replace("{{ head }}", head.group("content").strip("\n"))
        .replace("{{ body }}", body.group("content").strip("\n"))
    )

    if rendered.count(GTM_ID) != 2:
        raise ValueError("the shared layout must contain exactly two GTM container references")
    if rendered.count(posthog_token) != 1:
        raise ValueError("the shared layout must contain exactly one PostHog project token")
    return rendered.rstrip() + "\n"


def build(output: Path) -> list[Path]:
    layout = LAYOUT.read_text(encoding="utf-8")
    posthog_token = get_posthog_project_token()
    page_sources = sorted(PAGES.rglob("*.html"))
    if not page_sources:
        raise ValueError("site/pages contains no HTML pages")
    public_html = sorted(PUBLIC.rglob("*.html"))
    if public_html:
        paths = ", ".join(str(path.relative_to(ROOT)) for path in public_html)
        raise ValueError(
            f"public/ cannot contain HTML because it would bypass the shared layout: {paths}"
        )

    output = output.resolve()
    protected = {Path("/"), ROOT, Path.home().resolve(), PUBLIC.resolve(), PAGES.resolve()}
    if output in protected:
        raise ValueError(f"refusing to replace protected output directory: {output}")

    output.parent.mkdir(parents=True, exist_ok=True)
    staging = Path(tempfile.mkdtemp(prefix=".site-build-", dir=output.parent))
    try:
        shutil.copytree(PUBLIC, staging, dirs_exist_ok=True)
        for source in page_sources:
            destination = staging / source.relative_to(PAGES)
            if destination.exists():
                raise ValueError(f"page output conflicts with public asset: {destination.relative_to(staging)}")
            destination.parent.mkdir(parents=True, exist_ok=True)
            destination.write_text(
                render_page(source, layout, posthog_token), encoding="utf-8"
            )

        generated_pages = sorted(path.relative_to(staging) for path in staging.rglob("*.html"))
        if output.exists():
            shutil.rmtree(output)
        staging.replace(output)
        return generated_pages
    except Exception:
        shutil.rmtree(staging, ignore_errors=True)
        raise


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, default=ROOT / ".build")
    args = parser.parse_args()
    pages = build(args.output)
    print(f"Built {len(pages)} page(s) into {args.output.resolve()}")
    for page in pages:
        print(f"  {page}")


if __name__ == "__main__":
    main()
