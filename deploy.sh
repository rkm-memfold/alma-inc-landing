#!/usr/bin/env bash
#
# Deploy the landing page to the Azure VM behind alma.inc.
#
# Syncs every git-tracked file except the deploy tooling itself, then verifies
# each file over HTTPS by comparing checksums. See DEPLOY.md for infrastructure.
#
# Usage:
#   ./deploy.sh            deploy the current working tree
#   ./deploy.sh --pull     git pull --ff-only first, then deploy

set -euo pipefail

HOST="azureuser@168.61.34.144"
WEBROOT="/var/www/alma"
SITE="https://alma.inc"

# Tracked paths that must never be published — deploy docs leak infra details
# (subscription id, IP, ssh user) and the nginx snapshot is reference material.
is_excluded() {
  case "$1" in
    DEPLOY.md|POSTHOG_SETUP.md|deploy.sh|deploy/*|backend/*|.gitignore|README.md) return 0 ;;
    *) return 1 ;;
  esac
}

cd "$(git rev-parse --show-toplevel)"

if [[ "${1:-}" == "--pull" ]]; then
  echo "==> git pull --ff-only"
  git pull --ff-only
fi

# Warn but don't block: deploying a dirty tree is sometimes intentional.
if [[ -n "$(git status --porcelain --untracked-files=no)" ]]; then
  echo "!!  working tree has uncommitted changes to tracked files"
  git status --short --untracked-files=no
  echo
fi

git fetch --quiet origin 2>/dev/null || true
if [[ -n "$(git rev-list HEAD..origin/main --count 2>/dev/null || echo 0)" ]] \
   && [[ "$(git rev-list HEAD..origin/main --count 2>/dev/null || echo 0)" != "0" ]]; then
  echo "!!  local HEAD is behind origin/main — run with --pull to pick up remote commits"
  echo
fi

echo "==> deploying $(git rev-parse --short HEAD) to ${HOST}:${WEBROOT}"

# Stage the publishable subset so rsync --delete can prune removed files without
# us hand-maintaining a file list (the bug that nearly dropped llms.txt).
STAGE="$(mktemp -d)"
trap 'rm -rf "$STAGE"' EXIT

FILES=()
while IFS= read -r f; do
  is_excluded "$f" && continue
  mkdir -p "$STAGE/$(dirname "$f")"
  cp "$f" "$STAGE/$f"
  FILES+=("$f")
done < <(git ls-files)

if [[ ${#FILES[@]} -eq 0 ]]; then
  echo "no files to deploy" >&2
  exit 1
fi

printf '    %s\n' "${FILES[@]}"

# -a propagates the staging tree's modes, and mktemp -d creates 0700 — which
# would leave the webroot unreadable to anything but www-data. Normalize here
# rather than with rsync --chmod, which Apple's openrsync doesn't support.
find "$STAGE" -type d -exec chmod 755 {} +
find "$STAGE" -type f -exec chmod 644 {} +

# 'P .well-known' protects certbot's ACME challenge dir from --delete. Without
# it, --delete would remove it and break certificate renewal.
rsync -az --delete --filter='P .well-known' --rsync-path='sudo rsync' \
  "$STAGE/" "${HOST}:${WEBROOT}/"

ssh "$HOST" "sudo chown -R www-data:www-data ${WEBROOT}"

# Content-only changes need no nginx reload; nginx serves from disk per request.

echo
echo "==> verifying over ${SITE}"
FAILED=0
for f in "${FILES[@]}"; do
  # index.html is served at / — requesting /index.html would also work, but /
  # is what visitors actually hit, so verify the real path.
  url_path="$f"
  [[ "$f" == "index.html" ]] && url_path=""

  local_sum="$(shasum -a 256 "$f" | cut -d' ' -f1)"
  live_sum="$(curl -sS -m 20 "${SITE}/${url_path}" | shasum -a 256 | cut -d' ' -f1)"
  status="$(curl -sS -m 20 -o /dev/null -w '%{http_code}' "${SITE}/${url_path}")"

  if [[ "$local_sum" == "$live_sum" && "$status" == "200" ]]; then
    printf '    OK       %-20s (%s)\n' "$f" "$status"
  else
    printf '    MISMATCH %-20s (status=%s)\n' "$f" "$status"
    printf '             local=%s\n             live =%s\n' "$local_sum" "$live_sum"
    FAILED=1
  fi
done

echo
if [[ $FAILED -eq 0 ]]; then
  echo "==> deployed $(git rev-parse --short HEAD) — all ${#FILES[@]} files verified"
else
  echo "==> DEPLOY VERIFICATION FAILED" >&2
  exit 1
fi
