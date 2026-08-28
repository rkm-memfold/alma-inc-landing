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
