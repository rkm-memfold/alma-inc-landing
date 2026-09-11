// @ts-check
import { readdirSync, readFileSync, statSync } from "node:fs";
import { join } from "node:path";
import { fileURLToPath } from "node:url";
import { defineConfig } from "astro/config";

const GTM_ID = "GTM-T9SDSZMJ";

/**
 * The checks the previous Python build enforced, kept as a build step so the
 * guarantee survives the move to Astro: analytics lives in the shared layout
 * and nowhere else, and the PostHog token is injected exactly once.
 */
function analyticsGuards() {
  return {
    name: "alma:analytics-guards",
    hooks: {
      "astro:build:done": ({ dir, logger }) => {
        const root = fileURLToPath(dir);

        const pages = [];
        const walk = (directory) => {
          for (const entry of readdirSync(directory)) {
            const path = join(directory, entry);
            if (statSync(path).isDirectory()) walk(path);
            else if (entry.endsWith(".html")) pages.push(path);
          }
        };
        const walkPages = (directory) => {
          for (const entry of readdirSync(directory)) {
            const path = join(directory, entry);
            if (statSync(path).isDirectory()) {
              // fragments are not pages; they carry no layout and no analytics
              if (entry !== "windows") walkPages(path);
            } else if (entry.endsWith(".html")) pages.push(path);
          }
        };
        walkPages(root);

        if (pages.length === 0) {
          throw new Error("the build produced no pages");
        }

        for (const page of pages) {
          const html = readFileSync(page, "utf8");
          const relative = page.slice(root.length);

          const gtm = html.split(GTM_ID).length - 1;
          if (gtm !== 2) {
            throw new Error(
              `${relative} has ${gtm} references to ${GTM_ID}; the shared layout must contribute exactly two`
            );
          }

          const tokens = html.match(/phc_[A-Za-z0-9]+/g) ?? [];
          if (tokens.length !== 1) {
            throw new Error(
              `${relative} has ${tokens.length} PostHog project tokens; the shared layout must contribute exactly one`
            );
          }

          const inits = html.split("posthog.init").length - 1;
          if (inits !== 1) {
            throw new Error(
              `${relative} calls posthog.init ${inits} times; it belongs only in the shared layout`
            );
          }
        }

        logger.info(`analytics guards passed on ${pages.length} page(s)`);
      },
    },
  };
}


export default defineConfig({
  site: "https://alma.inc",

  // Keep the repository's existing shape: pages and the layout stay under
  // site/, everything served verbatim stays under public/, and the build lands
  // in .build, which is what deploy.sh and the VM's autodeploy already sync.
  srcDir: "./site",
  publicDir: "./public",
  outDir: process.env.ASTRO_OUT_DIR || "./.build",

  // /privacy/index.html rather than /privacy.html, matching the URLs the app
  // links to and nginx already serves.
  build: { format: "directory" },
  trailingSlash: "always",

  // The page is hand-written HTML, CSS and vanilla JS. Leaving it uncompressed
  // keeps the built output readable and diffable against what came before;
  // nginx gzips it on the way out either way.
  compressHTML: false,

  devToolbar: { enabled: false },

  integrations: [analyticsGuards()],
});
