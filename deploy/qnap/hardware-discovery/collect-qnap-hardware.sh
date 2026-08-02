#!/usr/bin/env sh
set -u

PROGRAM_NAME=${0##*/}
SCRIPT_DIR=$(CDPATH= cd -- "$(dirname -- "$0")" 2>/dev/null && pwd)
REPOSITORY_ROOT=$(CDPATH= cd -- "$SCRIPT_DIR/../../.." 2>/dev/null && pwd)
OUTPUT_DIR=
SHOW_HELP=0

usage() {
  cat <<USAGE
Usage: $PROGRAM_NAME --output-dir ABSOLUTE_DIRECTORY

Collect a read-only SALIG QNAP hardware and Container Station discovery report.
The output directory must be outside the Git repository. The script creates one
private (mode 0600) timestamped text file and does not start, stop, inspect the
environment of, or modify any container, network, volume, image, model, database,
or host configuration.

Options:
  --output-dir DIR   Required absolute directory for private evidence.
  -h, --help         Show this help text.
USAGE
}

fail() {
  printf '%s\n' "ERROR: $*" >&2
  exit 2
}

while [ "$#" -gt 0 ]; do
  case "$1" in
    --output-dir)
      [ "$#" -ge 2 ] || fail "--output-dir requires a value"
      OUTPUT_DIR=$2
      shift 2
      ;;
    -h|--help)
      SHOW_HELP=1
      shift
      ;;
    *)
      fail "unknown argument: $1"
      ;;
  esac
done

[ "$SHOW_HELP" -eq 0 ] || {
  usage
  exit 0
}

[ -n "$OUTPUT_DIR" ] || fail "--output-dir is required"
case "$OUTPUT_DIR" in
  /*) ;;
  *) fail "--output-dir must be an absolute path" ;;
esac

mkdir -p -- "$OUTPUT_DIR" || fail "cannot create output directory: $OUTPUT_DIR"
OUTPUT_DIR=$(CDPATH= cd -- "$OUTPUT_DIR" 2>/dev/null && pwd) || fail "cannot resolve output directory"
case "$OUTPUT_DIR/" in
  "$REPOSITORY_ROOT/"*) fail "output directory must be outside the Git repository: $REPOSITORY_ROOT" ;;
esac

umask 077
UTC_TIMESTAMP=$(date -u '+%Y%m%dT%H%M%SZ') || fail "date command failed"
OUTPUT_FILE="$OUTPUT_DIR/salig_qnap_hardware_discovery_${UTC_TIMESTAMP}.txt"
: > "$OUTPUT_FILE" || fail "cannot create output file: $OUTPUT_FILE"
chmod 600 "$OUTPUT_FILE" 2>/dev/null || :

COMMANDS_RUN=0
COMMANDS_UNAVAILABLE=0
COMMANDS_FAILED=0

line() {
  printf '%s\n' "$*" >> "$OUTPUT_FILE"
}

section() {
  line ""
  line "================================================================================"
  line "$1"
  line "================================================================================"
}

run_command() {
  DESCRIPTION=$1
  shift
  COMMANDS_RUN=$((COMMANDS_RUN + 1))
  line ""
  line "--- $DESCRIPTION"
  line "COMMAND: $*"
  if "$@" >> "$OUTPUT_FILE" 2>&1; then
    line "RESULT: OK"
  else
    STATUS=$?
    COMMANDS_FAILED=$((COMMANDS_FAILED + 1))
    line "RESULT: FAILED (exit $STATUS)"
  fi
}

run_if_available() {
  DESCRIPTION=$1
  COMMAND_NAME=$2
  shift 2
  if command -v "$COMMAND_NAME" >/dev/null 2>&1; then
    run_command "$DESCRIPTION" "$@"
  else
    COMMANDS_UNAVAILABLE=$((COMMANDS_UNAVAILABLE + 1))
    line ""
    line "--- $DESCRIPTION"
    line "RESULT: NOT AVAILABLE ($COMMAND_NAME)"
  fi
}

run_file_if_readable() {
  DESCRIPTION=$1
  FILE_PATH=$2
  if [ -r "$FILE_PATH" ]; then
    run_command "$DESCRIPTION" cat "$FILE_PATH"
  else
    COMMANDS_UNAVAILABLE=$((COMMANDS_UNAVAILABLE + 1))
    line ""
    line "--- $DESCRIPTION"
    line "RESULT: NOT READABLE ($FILE_PATH)"
  fi
}

line "SALIG QNAP READ-ONLY HARDWARE DISCOVERY"
line "FORMAT_VERSION=1"
line "COLLECTED_AT_UTC=$(date -u '+%Y-%m-%dT%H:%M:%SZ')"
line "COLLECTOR_PATH=$SCRIPT_DIR/$PROGRAM_NAME"
line "REPOSITORY_ROOT=$REPOSITORY_ROOT"
line "OUTPUT_FILE=$OUTPUT_FILE"
line "PRIVACY_CLASSIFICATION=PRIVATE_OPERATIONAL_EVIDENCE"
line "CONTENT_WARNING=Review and redact hostnames, paths, network names, addresses and image names before external sharing."
line "SAFETY=No container, service, network, volume, image, model, database or host configuration is modified by this collector."

section "1. HOST IDENTITY AND QNAP RELEASE"
run_if_available "Hostname" hostname hostname
run_if_available "Kernel and architecture" uname uname -a
run_file_if_readable "Operating-system release" /etc/os-release
if command -v getcfg >/dev/null 2>&1; then
  run_command "QNAP system model" getcfg System Model -f /etc/config/uLinux.conf
  run_command "QNAP firmware version" getcfg System Version -f /etc/config/uLinux.conf
  run_command "QNAP firmware build number" getcfg System 'Build Number' -f /etc/config/uLinux.conf
else
  COMMANDS_UNAVAILABLE=$((COMMANDS_UNAVAILABLE + 1))
  line ""
  line "--- Selected QNAP metadata fallback"
  if [ -r /etc/config/uLinux.conf ]; then
    grep -E '^(Model|Version|Build Number)[[:space:]]*=' /etc/config/uLinux.conf >> "$OUTPUT_FILE" 2>&1 || true
    line "RESULT: FALLBACK_USED"
  else
    line "RESULT: NOT AVAILABLE (getcfg and /etc/config/uLinux.conf)"
  fi
fi

section "2. CPU AND INSTRUCTION SET"
run_if_available "CPU topology and flags" lscpu lscpu
run_if_available "Configured processing units" getconf getconf _NPROCESSORS_ONLN
run_if_available "Available processing units" nproc nproc --all
if [ -r /proc/cpuinfo ]; then
  run_command "CPU model, cores and instruction flags" sh -c "grep -E '^(processor|model name|Hardware|vendor_id|cpu family|model[[:space:]]*:|stepping|cpu cores|siblings|flags|Features)[[:space:]]*:' /proc/cpuinfo"
else
  COMMANDS_UNAVAILABLE=$((COMMANDS_UNAVAILABLE + 1))
fi

section "3. MEMORY, LOAD AND CGROUPS"
run_if_available "Memory summary" free free -h
if [ -r /proc/meminfo ]; then
  run_command "Selected memory counters" sh -c "grep -E '^(MemTotal|MemFree|MemAvailable|Buffers|Cached|SwapCached|SwapTotal|SwapFree|HugePages_Total|HugePages_Free|Hugepagesize):' /proc/meminfo"
fi
run_if_available "Uptime and load" uptime uptime
run_file_if_readable "Kernel load averages" /proc/loadavg
run_if_available "Process and file limits" sh sh -c 'ulimit -a'
if [ -r /sys/fs/cgroup/cgroup.controllers ]; then
  run_file_if_readable "Cgroup v2 controllers" /sys/fs/cgroup/cgroup.controllers
else
  run_command "Cgroup mounts" sh -c "mount | grep -E 'type cgroup2?| on /sys/fs/cgroup' || true"
fi
run_if_available "Short virtual-memory sample" vmstat vmstat 1 5

section "4. STORAGE AND FILESYSTEMS"
run_if_available "Mounted filesystem capacity" df df -hT
run_if_available "Block devices without serial numbers" lsblk lsblk -e 7 -o NAME,TYPE,SIZE,FSTYPE,MOUNTPOINTS,ROTA,MODEL
run_file_if_readable "Linux software RAID state" /proc/mdstat
run_if_available "Inode capacity" df df -hi
run_if_available "Block-device performance sample" iostat iostat -xz 1 3

section "5. DOCKER AND CONTAINER STATION"
if command -v docker >/dev/null 2>&1; then
  run_command "Docker client and server versions" docker version
  run_command "Docker engine facts" docker info --format 'ServerVersion={{.ServerVersion}}\nOperatingSystem={{.OperatingSystem}}\nOSType={{.OSType}}\nArchitecture={{.Architecture}}\nCPUs={{.NCPU}}\nTotalMemoryBytes={{.MemTotal}}\nDockerRootDir={{.DockerRootDir}}\nDriver={{.Driver}}\nCgroupDriver={{.CgroupDriver}}\nCgroupVersion={{.CgroupVersion}}\nContainers={{.Containers}}\nContainersRunning={{.ContainersRunning}}\nImages={{.Images}}\nKernelVersion={{.KernelVersion}}'
  run_command "Docker disk usage" docker system df
  run_command "Running container inventory without environment or mounts" docker ps --no-trunc --format 'table {{.Names}}\t{{.Image}}\t{{.Status}}\t{{.Networks}}'
  run_command "Container resource snapshot" docker stats --no-stream --format 'table {{.Name}}\t{{.CPUPerc}}\t{{.MemUsage}}\t{{.MemPerc}}\t{{.PIDs}}'
  run_command "Docker network inventory" docker network ls --format 'table {{.Name}}\t{{.Driver}}\t{{.Scope}}\t{{.Internal}}'
  run_command "Docker network IPAM summary" sh -c 'for network in $(docker network ls -q); do docker network inspect --format "Name={{.Name}} Driver={{.Driver}} Internal={{.Internal}} IPAM={{json .IPAM.Config}}" "$network"; done'
else
  COMMANDS_UNAVAILABLE=$((COMMANDS_UNAVAILABLE + 1))
  line ""
  line "Docker is not available to the executing user."
fi
run_if_available "Docker Compose version" docker docker compose version

section "6. ACCELERATOR AND PCI DEVICES"
run_if_available "Relevant PCI devices" sh sh -c "lspci -nn 2>/dev/null | grep -Ei 'vga|3d|display|nvidia|amd|intel|neural|accelerator|coprocessor' || true"
run_if_available "NVIDIA runtime status" nvidia-smi nvidia-smi
run_command "GPU and accelerator device nodes" sh -c "ls -ld /dev/dri /dev/dri/* /dev/nvidia* /dev/kfd 2>/dev/null || true"

section "7. THERMAL VISIBILITY"
run_if_available "Hardware sensor report" sensors sensors
run_command "Kernel thermal zones" sh -c 'found=0; for zone in /sys/class/thermal/thermal_zone*; do [ -d "$zone" ] || continue; found=1; printf "zone=%s type=" "$zone"; cat "$zone/type" 2>/dev/null || true; printf "temp_millidegrees="; cat "$zone/temp" 2>/dev/null || true; done; [ "$found" -eq 1 ] || echo "No readable thermal zones"'

section "8. COLLECTION SUMMARY"
line "COMMANDS_RUN=$COMMANDS_RUN"
line "COMMANDS_UNAVAILABLE=$COMMANDS_UNAVAILABLE"
line "COMMANDS_FAILED=$COMMANDS_FAILED"
if [ "$COMMANDS_FAILED" -eq 0 ]; then
  line "DISCOVERY_RESULT=COLLECTED"
else
  line "DISCOVERY_RESULT=COLLECTED_WITH_GAPS"
fi
line "NEXT_ACTION=Keep this file private and submit it for SALIG hardware suitability review."

printf '%s\n' "Created private discovery evidence: $OUTPUT_FILE"
printf '%s\n' "Commands failed: $COMMANDS_FAILED; optional commands unavailable: $COMMANDS_UNAVAILABLE"
exit 0
