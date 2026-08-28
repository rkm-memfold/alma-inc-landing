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
#
# Prints lines the workflow parses: deployed=<sha> and status=ok.

set -euo pipefail

target="${1:-}"

/usr/local/bin/alma-autodeploy.sh

head="$(git -C /opt/alma-site rev-parse HEAD)"
echo "deployed=$head"

if [[ -n "$target" ]] && ! git -C /opt/alma-site merge-base --is-ancestor "$target" "$head"; then
  echo "::error::VM is at $head, which does not contain $target"
  exit 1
fi

echo "status=ok"
