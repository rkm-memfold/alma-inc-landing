# Site pages

Every public HTML page is built through `site/layout.html`. The layout owns the
Google Tag Manager snippets, so page source files must not copy GTM themselves.

Add a route by creating a complete HTML document below `site/pages/`. The path
is preserved in the generated site. For example, `site/pages/dictation/index.html`
becomes `/dictation/` and automatically receives GTM in `<head>` and immediately
after `<body>`.

Build locally with:

```sh
python3 scripts/build_site.py
```

The generated `.build/` directory is disposable and is not committed.

## The legal documents

`/terms` and `/privacy` are written as Markdown in `site/legal/` and rendered
into pages by `scripts/render_legal.py`. The generated
`site/pages/terms/index.html` and `site/pages/privacy/index.html` are committed
like any other page, so the build and the deploy are unchanged — nothing on the
VM needs to know about Markdown.

After editing a document, re-render and commit both:

```sh
python3 scripts/render_legal.py
```

They are the copies Alma links to from its sign-in gate, so the URLs
`https://alma.inc/terms` and `https://alma.inc/privacy` are a contract with
released builds of the app: keep them, and redirect if they ever move.
