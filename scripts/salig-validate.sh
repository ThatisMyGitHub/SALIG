#!/usr/bin/env sh
set -eu

SCRIPT_DIR=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
REPOSITORY_ROOT=$(CDPATH= cd -- "$SCRIPT_DIR/.." && pwd)
REQUIREMENTS="$SCRIPT_DIR/requirements-salig-validation.txt"

command -v python3 >/dev/null 2>&1 || {
  printf '%s\n' "SALIG validation failed: python3 is required" >&2
  exit 2
}

python3 - <<'PY' >/dev/null 2>&1 || {
import jsonschema
import yaml
PY
  printf '%s\n' "SALIG validation dependencies are missing." >&2
  printf '%s\n' "Install them with: python3 -m pip install -r $REQUIREMENTS" >&2
  exit 2
}

exec python3 "$SCRIPT_DIR/salig_validate.py" --root "$REPOSITORY_ROOT" "$@"
