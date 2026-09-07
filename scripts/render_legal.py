#!/usr/bin/env python3
"""Render the Markdown in site/legal into pages under site/pages.

The legal documents are written and reviewed as Markdown; the site is plain
static HTML built through the shared layout (scripts/build_site.py). So they are
rendered here, once, and the result is committed like any other page — the build
and the deploy stay exactly what they were, and nothing on the VM has to learn
about Markdown.

Run it after editing a document:

    python3 scripts/render_legal.py

The subset understood is the subset these documents use: ATX headings,
paragraphs, bullet lists (including items that wrap across source lines), pipe
tables with a header underline, bold, and links. Anything else is left as the
text it was written as, which is the safe failure for a legal document.
"""

from __future__ import annotations

import html
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LEGAL = ROOT / "site" / "legal"
PAGES = ROOT / "site" / "pages"
SITE = "https://alma.inc"

# The documents cite each other by file name, which is right beside them and
# wrong in a browser.
PATHS = {"terms.md": "/terms", "privacy.md": "/privacy"}

DOCUMENTS = {
    "terms": {
        "path": "terms",
        "title": "Terms and Conditions",
        "description": "The terms you agree to when you use Alma.",
        "other": ("Privacy Policy", "/privacy"),
    },
    "privacy": {
        "path": "privacy",
        "title": "Privacy Policy",
        "description": "What Alma collects, what it never collects, and the settings that decide.",
        "other": ("Terms and Conditions", "/terms"),
    },
}

INLINE_LINK = re.compile(r"\[(?P<text>[^\]]+)\]\((?P<href>[^)]+)\)")
BOLD = re.compile(r"\*\*(?P<text>[^*]+)\*\*")


def inline(text: str) -> str:
    """Bold and links, on already-escaped text."""
    rendered = html.escape(text, quote=False)

    def link(match: re.Match[str]) -> str:
        href = PATHS.get(match.group("href"), match.group("href"))
        return f'<a href="{html.escape(href, quote=True)}">{bold(match.group("text"))}</a>'

    rendered = INLINE_LINK.sub(link, rendered)
    return bold(rendered)


def bold(text: str) -> str:
    return BOLD.sub(lambda match: f"<strong>{match.group('text')}</strong>", text)


def cells(row: str) -> list[str]:
    line = row.strip()
    if line.startswith("|"):
        line = line[1:]
    if line.endswith("|"):
        line = line[:-1]
    return [cell.strip() for cell in line.split("|")]


def underlines(row: list[str]) -> bool:
    return bool(row) and all(cell and set(cell) <= set("-:") for cell in row)


def render(markdown: str) -> tuple[str, str]:
    """The document's own title, and its body as HTML."""
    title = ""
    out: list[str] = []
    paragraph: list[str] = []
    bullets: list[str] = []
    rows: list[list[str]] = []
    headed = False

    def close_paragraph() -> None:
        nonlocal paragraph
        if paragraph:
            out.append(f"<p>{inline(' '.join(paragraph))}</p>")
            paragraph = []

    def close_bullets() -> None:
        nonlocal bullets
        if bullets:
            items = "".join(f"<li>{inline(item)}</li>" for item in bullets)
            out.append(f"<ul>{items}</ul>")
            bullets = []

    def close_table() -> None:
        nonlocal rows, headed
        if rows:
            head, body = (rows[0], rows[1:]) if headed and len(rows) > 1 else ([], rows)
            parts = ["<div class=\"table-scroll\"><table>"]
            if head:
                parts.append(
                    "<thead><tr>"
                    + "".join(f"<th>{inline(cell)}</th>" for cell in head)
                    + "</tr></thead>"
                )
            parts.append("<tbody>")
            for row in body:
                parts.append(
                    "<tr>" + "".join(f"<td>{inline(cell)}</td>" for cell in row) + "</tr>"
                )
            parts.append("</tbody></table></div>")
            out.append("".join(parts))
            rows = []
            headed = False

    for raw in markdown.split("\n"):
        line = raw.strip()
        if not line:
            close_paragraph()
            close_bullets()
            close_table()
        elif line.startswith("#"):
            close_paragraph()
            close_bullets()
            close_table()
            level = len(line) - len(line.lstrip("#"))
            text = line[level:].strip()
            if level == 1 and not title:
                title = text
            else:
                # Section headings are the document's own anchors, so a link to
                # a clause survives being sent to somebody.
                anchor = re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")
                out.append(
                    f'<h{level} id="{anchor}">'
                    f'<a class="anchor" href="#{anchor}">{inline(text)}</a>'
                    f"</h{level}>"
                )
        elif line[:2] in ("- ", "* ", "+ "):
            close_paragraph()
            close_table()
            bullets.append(line[2:])
        elif line.startswith("|"):
            close_paragraph()
            close_bullets()
            row = cells(line)
            if underlines(row):
                headed = True
            else:
                rows.append(row)
        elif bullets:
            # An item that wrapped in the source is still that item.
            bullets[-1] += " " + line
        else:
            close_table()
            paragraph.append(line)

    close_paragraph()
    close_bullets()
    close_table()
    return title, "\n        ".join(out)


PAGE = """<!DOCTYPE html>
<html lang="en">
  <head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <meta name="description" content="{description}">
    <meta name="robots" content="index,follow,max-image-preview:large,max-snippet:-1">
    <meta name="theme-color" content="#f7f7fb">
    <link rel="canonical" href="{site}/{path}">

    <meta property="og:title" content="{title} - Alma">
    <meta property="og:description" content="{description}">
    <meta property="og:type" content="article">
    <meta property="og:url" content="{site}/{path}">
    <meta property="og:site_name" content="Alma">
    <meta property="og:locale" content="en_US">
    <meta property="og:image" content="{site}/og-alma-wordmark.png">
    <meta property="og:image:type" content="image/png">
    <meta property="og:image:width" content="1200">
    <meta property="og:image:height" content="630">
    <meta property="og:image:alt" content="Alma, an AI-native computer interface">

    <meta name="twitter:card" content="summary_large_image">
    <meta name="twitter:site" content="@thinkwithalma">
    <meta name="twitter:title" content="{title} - Alma">
    <meta name="twitter:description" content="{description}">
    <meta name="twitter:image" content="{site}/og-alma-wordmark.png">

    <title>{title} - Alma</title>
    <link rel="icon" href="/client-logomark-dark.svg" type="image/svg+xml">
    <link rel="apple-touch-icon" href="/client-logomark-dark.png">

    <script type="application/ld+json">
      {{
        "@context": "https://schema.org",
        "@type": "WebPage",
        "name": "{title}",
        "description": "{description}",
        "url": "{site}/{path}",
        "inLanguage": "en",
        "isPartOf": {{ "@id": "{site}/#website" }},
        "publisher": {{ "@id": "{site}/#organization" }}
      }}
    </script>

    <style>
      @font-face {{
        font-family: "Miranda Sans";
        src: url("/page/fonts/miranda-400.ttf") format("truetype");
        font-style: normal;
        font-weight: 400;
        font-display: swap;
      }}

      @font-face {{
        font-family: "Miranda Sans";
        src: url("/page/fonts/miranda-500.ttf") format("truetype");
        font-style: normal;
        font-weight: 500;
        font-display: swap;
      }}

      @font-face {{
        font-family: "Miranda Sans";
        src: url("/page/fonts/miranda-700.ttf") format("truetype");
        font-style: normal;
        font-weight: 700;
        font-display: swap;
      }}

      :root {{
        color-scheme: light;
        --ink: #0d0818;
        --muted: #5d5a66;
        --line: rgba(13, 8, 24, 0.12);
      }}

      * {{
        box-sizing: border-box;
      }}

      body {{
        margin: 0;
        color: var(--ink);
        background: #f7f7fb;
        font-family: "Miranda Sans", -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
        font-size: 16px;
        line-height: 1.65;
      }}

      .brand {{
        display: inline-flex;
        align-items: center;
        padding: clamp(28px, 5vh, 48px) 0 0;
        color: var(--ink);
        line-height: 1;
        text-decoration: none;
      }}

      .brand img {{
        width: 92px;
        height: auto;
        display: block;
      }}

      .document {{
        width: min(46rem, 100% - 48px);
        margin: 0 auto;
        padding-bottom: clamp(56px, 9vh, 96px);
      }}

      h1 {{
        margin: clamp(28px, 5vh, 44px) 0 8px;
        font-size: clamp(28px, 4.2vw, 38px);
        font-weight: 700;
        line-height: 1.15;
        letter-spacing: -0.01em;
        text-wrap: balance;
      }}

      h2 {{
        margin: 40px 0 8px;
        font-size: 20px;
        font-weight: 700;
        line-height: 1.3;
      }}

      h3 {{
        margin: 28px 0 6px;
        font-size: 17px;
        font-weight: 500;
      }}

      .anchor {{
        color: inherit;
        text-decoration: none;
      }}

      .anchor:hover {{
        text-decoration: underline;
        text-underline-offset: 4px;
      }}

      p {{
        margin: 0 0 16px;
      }}

      ul {{
        margin: 0 0 16px;
        padding-left: 22px;
      }}

      li {{
        margin: 6px 0;
      }}

      a {{
        color: var(--ink);
        text-decoration: underline;
        text-underline-offset: 3px;
        text-decoration-thickness: 1px;
        text-decoration-color: rgba(13, 8, 24, 0.35);
      }}

      a:hover {{
        text-decoration-color: var(--ink);
      }}

      .table-scroll {{
        overflow-x: auto;
        margin: 0 0 20px;
      }}

      table {{
        width: 100%;
        border-collapse: collapse;
        font-size: 15px;
      }}

      th {{
        padding: 10px 16px 10px 0;
        border-bottom: 1px solid var(--line);
        font-weight: 500;
        text-align: left;
        vertical-align: top;
      }}

      td {{
        padding: 12px 16px 12px 0;
        border-bottom: 1px solid var(--line);
        color: var(--muted);
        vertical-align: top;
      }}

      tr td:first-child {{
        color: var(--ink);
        white-space: nowrap;
      }}

      @media (max-width: 640px) {{
        tr td:first-child {{
          white-space: normal;
        }}
      }}

      .document-footer {{
        margin-top: 48px;
        padding-top: 20px;
        border-top: 1px solid var(--line);
        color: var(--muted);
        font-size: 15px;
      }}

      .document-footer a {{
        color: var(--muted);
      }}
    </style>
  </head>
  <body>
    <div class="document">
      <a class="brand" href="/" aria-label="Alma home">
        <img src="/client-logo-dark.svg" alt="Alma">
      </a>
      <main>
        <h1>{heading}</h1>
        {body}
      </main>
      <footer class="document-footer">
        <a href="{other_href}">{other_title}</a> &middot; <a href="/">alma.inc</a>
      </footer>
    </div>
  </body>
</html>
"""


def main() -> None:
    written = []
    for name, meta in DOCUMENTS.items():
        source = LEGAL / f"{name}.md"
        heading, body = render(source.read_text(encoding="utf-8"))
        other_title, other_href = meta["other"]
        page = PAGE.format(
            site=SITE,
            path=meta["path"],
            title=meta["title"],
            description=meta["description"],
            heading=html.escape(heading, quote=False),
            body=body,
            other_title=other_title,
            other_href=other_href,
        )
        destination = PAGES / meta["path"] / "index.html"
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_text(page, encoding="utf-8")
        written.append(destination.relative_to(ROOT))
    for path in written:
        print(f"  {path}")


if __name__ == "__main__":
    main()
