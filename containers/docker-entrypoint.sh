#!/usr/bin/env bash
# Strix Web3 sandbox entrypoint.
#
# The sandbox is a plain tool container: no proxy sidecar or browser daemon to
# start. This entrypoint prepares the workspace and then runs whatever command
# the runtime passes, defaulting to a long-lived sleep so the session stays up.
set -euo pipefail

WORKSPACE="${WORKSPACE:-/workspace}"
mkdir -p "${WORKSPACE}"

# Make the audit toolchain resolvable in non-login shells too.
export PATH="/home/auditor/.venv/bin:/home/auditor/.foundry/bin:/home/auditor/.local/bin:${PATH}"

# Foundry/Docker sometimes runs as root; keep the workspace usable for the
# sandbox user when we can.
if [ "$(id -u)" = "0" ] && id auditor >/dev/null 2>&1; then
    chown -R auditor:auditor "${WORKSPACE}" 2>/dev/null || true
fi

if [ "$#" -eq 0 ]; then
    exec sleep infinity
fi

exec "$@"
