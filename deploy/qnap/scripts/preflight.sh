#!/usr/bin/env sh
set -eu

SCRIPT_DIR=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
DEPLOY_DIR=$(CDPATH= cd -- "$SCRIPT_DIR/.." && pwd)
ENV_FILE="$DEPLOY_DIR/.env"
COMPOSE_FILE="$DEPLOY_DIR/compose.yaml"
ALLOWLIST_FILE="$DEPLOY_DIR/../../salig/model-allowlist.yaml"

fail() {
  printf '%s\n' "SALIG preflight failed: $*" >&2
  exit 1
}

require_command() {
  command -v "$1" >/dev/null 2>&1 || fail "required command not found: $1"
}

require_value() {
  name=$1
  eval "value=\${$name:-}"
  [ -n "$value" ] || fail "$name is not set"
}

require_command docker
require_command grep
require_command sha256sum

[ -f "$ENV_FILE" ] || fail "missing $ENV_FILE; copy .env.example to .env and replace placeholders"
[ -f "$COMPOSE_FILE" ] || fail "missing $COMPOSE_FILE"
[ -f "$ALLOWLIST_FILE" ] || fail "missing $ALLOWLIST_FILE"

# The deployment .env is administrator-controlled and must contain simple
# shell-compatible KEY=VALUE assignments.
set -a
# shellcheck disable=SC1090
. "$ENV_FILE"
set +a

require_value SALIG_LOCALAI_IMAGE
require_value SALIG_API_KEY
require_value SALIG_DATA_ROOT
require_value SALUTAPP_INTERNAL_NETWORK

case "$SALIG_LOCALAI_IMAGE" in
  *@sha256:*) ;;
  *) fail "SALIG_LOCALAI_IMAGE is not pinned by digest" ;;
esac

IMAGE_DIGEST=${SALIG_LOCALAI_IMAGE##*@sha256:}
case "$IMAGE_DIGEST" in
  *[!0-9a-fA-F]*) fail "image digest contains non-hexadecimal characters" ;;
esac
[ "${#IMAGE_DIGEST}" -eq 64 ] || fail "image digest must contain exactly 64 hexadecimal characters"

case "$SALIG_LOCALAI_IMAGE" in
  *REPLACE*|*replace*|*latest*|*:master|*:master-*)
    fail "image reference still contains a placeholder or floating tag"
    ;;
esac

case "$SALIG_API_KEY" in
  *REPLACE*|*replace*) fail "SALIG_API_KEY still contains a placeholder" ;;
esac
[ "${#SALIG_API_KEY}" -ge 32 ] || fail "SALIG_API_KEY must contain at least 32 characters"

[ -d "$SALIG_DATA_ROOT" ] || fail "data root does not exist: $SALIG_DATA_ROOT"
[ -d "$SALIG_DATA_ROOT/models" ] || fail "model directory does not exist: $SALIG_DATA_ROOT/models"
[ -d "$SALIG_DATA_ROOT/data" ] || fail "runtime data directory does not exist: $SALIG_DATA_ROOT/data"

if grep -Eq '^[[:space:]]+ports:' "$COMPOSE_FILE"; then
  fail "compose.yaml publishes a host port; SALIG must remain internal-only"
fi

if grep -Eq '^models:[[:space:]]*\[\][[:space:]]*$' "$ALLOWLIST_FILE"; then
  fail "the model allowlist contains no approved model"
fi

docker network inspect "$SALUTAPP_INTERNAL_NETWORK" >/dev/null 2>&1 \
  || fail "Docker network not found: $SALUTAPP_INTERNAL_NETWORK"

docker compose \
  --project-directory "$DEPLOY_DIR" \
  --env-file "$ENV_FILE" \
  -f "$COMPOSE_FILE" \
  config >/dev/null \
  || fail "Docker Compose configuration validation failed"

printf '%s\n' "SALIG preflight passed. No container was started."
