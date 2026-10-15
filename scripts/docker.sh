#!/bin/bash
set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

IMAGE="strix-sandbox"
TAG="${1:-dev}"
EXTRA_CHAINS="${INSTALL_EXTRA_CHAINS:-1}"

echo "Building $IMAGE:$TAG (INSTALL_EXTRA_CHAINS=$EXTRA_CHAINS) ..."
docker build \
  --build-arg "INSTALL_EXTRA_CHAINS=$EXTRA_CHAINS" \
  -f "$PROJECT_ROOT/containers/Dockerfile" \
  -t "$IMAGE:$TAG" \
  "$PROJECT_ROOT"

echo "Done: $IMAGE:$TAG"
