#!/usr/bin/env bash
#
# Deploy the landing page to the Azure VM behind alma.inc.
#
# Builds every page through the shared layout, syncs the generated site, then
# verifies each file over HTTPS by comparing checksums. See DEPLOY.md.
#
# Usage:
#   ./deploy.sh            deploy the current working tree
#   ./deploy.sh --pull     git pull --ff-only first, then deploy

set -euo pipefail

HOST="azureuser@168.61.34.144"
WEBROOT="/var/www/alma"
SITE="https://alma.inc"

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

# Build into a disposable staging directory. Only files in public/ and generated
# pages can reach the webroot; source, backend, docs, and tooling stay private.
STAGE="$(mktemp -d)"
trap 'rm -rf "$STAGE"' EXIT

python3 scripts/build_site.py --output "$STAGE"

FILES=()
while IFS= read -r -d '' f; do
  FILES+=("${f#"$STAGE"/}")
done < <(find "$STAGE" -type f -print0)

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

  local_sum="$(shasum -a 256 "$STAGE/$f" | cut -d' ' -f1)"
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
