#!/usr/bin/env sh
set -eu

PROGRAM_NAME=${0##*/}

usage() {
  printf '%s\n' "Usage: $PROGRAM_NAME ABSOLUTE_EVIDENCE_FILE"
}

[ "$#" -eq 1 ] || {
  usage >&2
  exit 2
}

EVIDENCE_FILE=$1
case "$EVIDENCE_FILE" in
  /*) ;;
  *) printf '%s\n' "ERROR: evidence file path must be absolute" >&2; exit 2 ;;
esac

[ -f "$EVIDENCE_FILE" ] || {
  printf '%s\n' "ERROR: evidence file not found: $EVIDENCE_FILE" >&2
  exit 2
}
[ -r "$EVIDENCE_FILE" ] || {
  printf '%s\n' "ERROR: evidence file is not readable: $EVIDENCE_FILE" >&2
  exit 2
}

required_lines='SALIG QNAP READ-ONLY HARDWARE DISCOVERY
FORMAT_VERSION=1
1. HOST IDENTITY AND QNAP RELEASE
2. CPU AND INSTRUCTION SET
3. MEMORY, LOAD AND CGROUPS
4. STORAGE AND FILESYSTEMS
5. DOCKER AND CONTAINER STATION
6. ACCELERATOR AND PCI DEVICES
7. THERMAL VISIBILITY
8. COLLECTION SUMMARY
DISCOVERY_RESULT='

printf '%s\n' "$required_lines" | while IFS= read -r marker; do
  [ -n "$marker" ] || continue
  grep -F "$marker" "$EVIDENCE_FILE" >/dev/null 2>&1 || {
    printf '%s\n' "ERROR: missing evidence marker: $marker" >&2
    exit 3
  }
done

if command -v sha256sum >/dev/null 2>&1; then
  CHECKSUM=$(sha256sum "$EVIDENCE_FILE" | awk '{print $1}')
elif command -v shasum >/dev/null 2>&1; then
  CHECKSUM=$(shasum -a 256 "$EVIDENCE_FILE" | awk '{print $1}')
else
  printf '%s\n' "ERROR: sha256sum or shasum is required" >&2
  exit 2
fi

printf '%s\n' "EVIDENCE_STRUCTURE=VALID"
grep -E '^(COLLECTED_AT_UTC|COMMANDS_RUN|COMMANDS_UNAVAILABLE|COMMANDS_FAILED|DISCOVERY_RESULT)=' "$EVIDENCE_FILE" || true
printf '%s\n' "EVIDENCE_SHA256=$CHECKSUM"
printf '%s\n' "EVIDENCE_FILE=$EVIDENCE_FILE"
