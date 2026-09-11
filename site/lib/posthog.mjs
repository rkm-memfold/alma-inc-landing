import { readFileSync } from "node:fs";

// On the VM the token is written to a root-only file by the deploy scripts;
// locally and in CI it arrives through the environment.
const TOKEN_FILE = "/etc/alma-posthog-project-token";

export function posthogProjectToken() {
  let token = (process.env.POSTHOG_PROJECT_TOKEN ?? "").trim();

  if (!token) {
    try {
      token = readFileSync(TOKEN_FILE, "utf8").trim();
    } catch {
      // fall through to the error below, which says what to do about it
    }
  }

  if (!/^phc_[A-Za-z0-9]+$/.test(token)) {
    throw new Error(
      `POSTHOG_PROJECT_TOKEN must be supplied through the environment or ${TOKEN_FILE}`
    );
  }

  return token;
}
