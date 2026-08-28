#!/usr/bin/env bash
#
# Auto-deploy the landing page when origin/main moves.
#
# Runs on the VM as root, both from alma-autodeploy.timer (poll every 2 min)
# and on demand from the GitHub Actions deploy workflow via `az vm run-command`
# (see deploy/gha-remote-deploy.sh). Polls the public GitHub repo over
# read-only HTTPS, so there are no credentials anywhere in this path.
# Static files only — backend changes still need a migrate + service restart,
# so those stay manual (see DEPLOY.md).
#
# Pass --force to rebuild and resync even when HEAD already matches origin/main
# (e.g. after changing this script or the build tooling).
#
# Installed at /usr/local/bin/alma-autodeploy.sh

set -euo pipefail

REPO="/opt/alma-site"
WEBROOT="/var/www/alma"
FORCE=0
[[ "${1:-}" == "--force" ]] && FORCE=1

cd "$REPO"

git fetch --quiet origin main

if [[ "$FORCE" -eq 0 && "$(git rev-parse HEAD)" == "$(git rev-parse origin/main)" ]]; then
  exit 0
fi

# Hard reset rather than pull: this clone is deploy-only and never edited, so
# there is nothing to preserve, and a reset cannot fail on a diverged tree.
git reset --hard --quiet origin/main

# Mirrors deploy.sh: build every page through site/layout.html into a
# disposable staging directory. Only generated pages and public/ can reach the
# webroot, so docs, backend code, scripts, and templates are never served.
# If the build fails, set -e aborts before rsync and the webroot is untouched.
STAGE="$(mktemp -d)"
trap 'rm -rf "$STAGE"' EXIT

python3 scripts/build_site.py --output "$STAGE"

# Normalize permissions so nginx can read the tree.
find "$STAGE" -type d -exec chmod 755 {} +
find "$STAGE" -type f -exec chmod 644 {} +

# 'P .well-known' keeps certbot's ACME challenge dir safe from --delete.
rsync -a --delete --filter='P .well-known' "$STAGE/" "$WEBROOT/"
chown -R www-data:www-data "$WEBROOT"

logger -t alma-autodeploy "deployed $(git rev-parse --short HEAD)"
