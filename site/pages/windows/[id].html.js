import { WINDOW_HTML } from "../../content/windows.mjs";

// One small fragment per window, so the desktop can fill a window the current
// route did not ship. Not pages: robots.txt keeps them out of the index.
export function getStaticPaths() {
  return Object.keys(WINDOW_HTML).map((id) => ({ params: { id } }));
}

export function GET({ params }) {
  return new Response(WINDOW_HTML[params.id] ?? "", {
    headers: {
      "Content-Type": "text/html; charset=utf-8",
      "X-Robots-Tag": "noindex",
    },
  });
}
