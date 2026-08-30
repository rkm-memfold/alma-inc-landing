#!/usr/bin/env bash
#
# Runs on the VM, as root, via `az vm run-command invoke` from the GitHub
# Actions deploy workflow. It only triggers the VM's own autodeploy script and
# reports what ended up deployed, so the workflow holds no deploy logic and no
# credentials beyond the OIDC-scoped run-command permission.
#
# $1: the commit the workflow is deploying. The VM always deploys origin/main,
#     which may already be ahead if another push landed first; that is fine as
#     long as it contains $1.
# $2: the PostHog project token, supplied by GitHub Actions secrets and written
#     to a root-only build configuration file before the site build runs.
#
# Prints lines the workflow parses: deployed=<sha> and status=ok.

set -euo pipefail

target="${1:-}"
posthog_token="${2:-}"

if [[ ! "$posthog_token" =~ ^phc_[[:alnum:]]+$ ]]; then
  echo "::error::missing or invalid PostHog project token"
  exit 1
fi

umask 077
printf '%s\n' "$posthog_token" > /etc/alma-posthog-project-token
unset posthog_token

/usr/local/bin/alma-autodeploy.sh

head="$(git -C /opt/alma-site rev-parse HEAD)"
echo "deployed=$head"

if [[ -n "$target" ]] && ! git -C /opt/alma-site merge-base --is-ancestor "$target" "$head"; then
  echo "::error::VM is at $head, which does not contain $target"
  exit 1
fi

echo "status=ok"
