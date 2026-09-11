/**
 * The sitemap, generated rather than hand-maintained.
 *
 * lastmod used to be a hardcoded date, which is worse than omitting it: it
 * goes stale silently and Google learns to distrust it. Here each URL takes
 * the commit date of the files that actually produce it, so a page claims to
 * have changed exactly when it did. If git is unavailable the date is dropped
 * for that URL rather than guessed at.
 *
 * The two videos are declared on the pages that show them, not on the
 * homepage, matching where the VideoObject markup now lives.
 */
import { execFileSync } from "node:child_process";

const SHELL = [
  "site/components/Desktop.astro",
  "site/components/DesktopHead.astro",
  "site/components/Wallpaper.astro",
  "site/content/windows.mjs",
];

const VIDEOS = {
  blender: {
    title: "Alma builds a rocket in Blender with computer use",
    description:
      "Alma opens Blender on a Mac and models a rocket end to end using computer use. Under two minutes, about $0.30. Filmed off the screen, uncut.",
    duration: 117,
  },
  paint: {
    title: "Alma paints in MS Paint by voice",
    description:
      "Alma drives MS Paint by voice, using the brush, the palette and the fill tool, the same surface a person would use.",
    duration: 53,
  },
};

const PAGES = [
  { loc: "/", priority: "1.0", changefreq: "weekly", sources: ["site/pages/index.astro", ...SHELL] },
  { loc: "/demos/", priority: "0.9", changefreq: "monthly", sources: ["site/pages/demos/index.astro", ...SHELL] },
  { loc: "/demos/blender/", priority: "0.8", changefreq: "monthly", video: "blender", sources: ["site/pages/demos/blender/index.astro", ...SHELL] },
  { loc: "/demos/paint/", priority: "0.8", changefreq: "monthly", video: "paint", sources: ["site/pages/demos/paint/index.astro", ...SHELL] },
  { loc: "/manifesto/", priority: "0.8", changefreq: "monthly", sources: ["site/pages/manifesto/index.astro", ...SHELL] },
  { loc: "/join-us/", priority: "0.7", changefreq: "monthly", sources: ["site/pages/join-us/index.astro", ...SHELL] },
  { loc: "/socials/", priority: "0.4", changefreq: "yearly", sources: ["site/pages/socials/index.astro", ...SHELL] },
  { loc: "/privacy/", priority: "0.3", changefreq: "yearly", sources: ["site/pages/privacy/index.astro"] },
  { loc: "/terms/", priority: "0.3", changefreq: "yearly", sources: ["site/pages/terms/index.astro"] },
];

function lastCommit(paths) {
  let newest = null;
  for (const path of paths) {
    try {
      const stamp = execFileSync("git", ["log", "-1", "--format=%cs", "--", path], {
        encoding: "utf8",
        stdio: ["ignore", "pipe", "ignore"],
      }).trim();
      if (stamp && (!newest || stamp > newest)) newest = stamp;
    } catch {
      // no git, or the file is not committed yet: fall through
    }
  }
  return newest;
}

const escape = (text) =>
  text.replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;");

export function GET() {
  const body = PAGES.map((page) => {
    const modified = lastCommit(page.sources);
    const video = page.video ? VIDEOS[page.video] : null;
    return [
      "  <url>",
      `    <loc>https://alma.inc${page.loc}</loc>`,
      modified ? `    <lastmod>${modified}</lastmod>` : null,
      `    <changefreq>${page.changefreq}</changefreq>`,
      `    <priority>${page.priority}</priority>`,
      video
        ? [
            "    <video:video>",
            `      <video:thumbnail_loc>https://alma.inc/page/desktop/demos/${page.video}-poster.jpg</video:thumbnail_loc>`,
            `      <video:title>${escape(video.title)}</video:title>`,
            `      <video:description>${escape(video.description)}</video:description>`,
            `      <video:content_loc>https://alma.inc/page/desktop/demos/${page.video}.mp4</video:content_loc>`,
            `      <video:duration>${video.duration}</video:duration>`,
            "      <video:family_friendly>yes</video:family_friendly>",
            "    </video:video>",
          ].join("\n")
        : null,
      "  </url>",
    ]
      .filter(Boolean)
      .join("\n");
  }).join("\n");

  return new Response(
    `<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9"
        xmlns:video="http://www.google.com/schemas/sitemap-video/1.1">
${body}
</urlset>
`,
    { headers: { "Content-Type": "application/xml; charset=utf-8" } }
  );
}
