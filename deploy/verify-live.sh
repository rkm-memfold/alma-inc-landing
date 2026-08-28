#!/usr/bin/env bash
#
# Verify a built site directory against the live site: every file must match by
# sha256, and repo internals must not be reachable from the webroot. Used by the
# GitHub Actions deploy workflow; also works locally after
# `python3 scripts/build_site.py --output .build`.
#
# Usage: deploy/verify-live.sh <build-dir>   (SITE overrides https://alma.inc)

set -euo pipefail

build="${1:?usage: verify-live.sh <build-dir>}"
site="${SITE:-https://alma.inc}"

sha256() {
  if command -v sha256sum >/dev/null 2>&1; then sha256sum | cut -d' ' -f1
  else shasum -a 256 | cut -d' ' -f1
  fi
}

fail=0

while IFS= read -r -d '' f; do
  rel="${f#"$build"/}"
  url_path="$rel"
  case "$rel" in
    index.html) url_path="" ;;
    */index.html) url_path="${rel%index.html}" ;;
  esac
  local_sum="$(sha256 < "$f")"
  live_sum="$(curl -sS -m 20 "${site}/${url_path}" | sha256)"
  if [[ "$local_sum" == "$live_sum" ]]; then
    echo "ok       /${url_path}"
  else
    echo "MISMATCH /${url_path}"
    fail=1
  fi
done < <(find "$build" -type f -print0)

# Anything tracked outside public/ and site/pages/ must never be served.
for p in site/layout.html site/pages/index.html scripts/build_site.py DEPLOY.md deploy.sh deploy/nginx-alma.conf; do
  code="$(curl -sS -m 20 -o /dev/null -w '%{http_code}' "${site}/${p}")"
  if [[ "$code" == "404" ]]; then
    echo "ok       /${p} -> 404"
  else
    echo "EXPOSED  /${p} -> ${code}"
    fail=1
  fi
done

exit "$fail"
