#!/usr/bin/env python3
"""Static policy validation for SALIG-owned repository content."""

from __future__ import annotations

import argparse
import datetime as dt
import json
from pathlib import Path
import re
import shlex
import shutil
import subprocess
import tempfile
import sys
from typing import Any, Iterable, Mapping, Sequence

try:
    import yaml
    from jsonschema import Draft202012Validator, FormatChecker
except ImportError as exc:  # pragma: no cover - handled by shell entry point
    print(
        "SALIG validation dependencies are missing. Install "
        "scripts/requirements-salig-validation.txt.",
        file=sys.stderr,
    )
    raise SystemExit(2) from exc


HEX64 = re.compile(r"^[0-9a-f]{64}$")
HEX40 = re.compile(r"^[0-9a-f]{40}$")
IMAGE_WITH_DIGEST = re.compile(r"^[^\s@]+@sha256:[0-9a-f]{64}$")
REPOSITORY_NAME = re.compile(r"^[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+$")
BRANCH_NAME = re.compile(r"^(?!/)(?!.*//)(?!.*\.\.)[A-Za-z0-9._/-]+(?<!/)$")
PLACEHOLDER = re.compile(r"(?i)(replace|placeholder|changeme|example|todo|tbd|<[^>]+>|x{4,})")
DB_CREDENTIAL_NAME = re.compile(
    r"\b(?:MYSQL|MARIADB|DATABASE_URL|DB_(?:HOST|PORT|NAME|USER|USERNAME|PASSWORD|PASS))\b",
    re.IGNORECASE,
)
PRIVATE_KEY_MARKER = re.compile(
    r"-----BEGIN (?:RSA |EC |OPENSSH |DSA |ENCRYPTED )?PRIVATE KEY-----"
)
SECRET_TOKEN_PATTERNS = (
    re.compile(r"\bgithub_pat_[A-Za-z0-9_]{20,}\b"),
    re.compile(r"\bghp_[A-Za-z0-9]{30,}\b"),
    re.compile(r"\bsk_live_[A-Za-z0-9]{16,}\b"),
    re.compile(r"\bwhsec_[A-Za-z0-9]{20,}\b"),
    re.compile(r"\bxox[baprs]-[A-Za-z0-9-]{20,}\b"),
    re.compile(r"\bAKIA[0-9A-Z]{16}\b"),
)

SALIG_PATH_PREFIXES = (
    "salig/",
    "deploy/qnap/",
    "docs/salig/",
    "tests/salig-validation/",
    ".github/workflows/salig-",
)
SALIG_EXACT_PATHS = {"SALIG.md", "scripts/salig-validate.sh", "scripts/salig_validate.py", "scripts/requirements-salig-validation.txt"}


class ValidationErrors:
    def __init__(self) -> None:
        self.items: list[str] = []

    def add(self, message: str) -> None:
        self.items.append(message)

    def require(self, condition: bool, message: str) -> None:
        if not condition:
            self.add(message)


def parse_env_file(path: Path, errors: ValidationErrors) -> dict[str, str]:
    values: dict[str, str] = {}
    try:
        lines = path.read_text(encoding="utf-8").splitlines()
    except OSError as exc:
        errors.add(f"cannot read environment file {path}: {exc}")
        return values

    for number, raw in enumerate(lines, start=1):
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        if line.startswith("export "):
            line = line[7:].lstrip()
        if "=" not in line:
            errors.add(f"{path}:{number}: expected KEY=VALUE assignment")
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip()
        if not re.fullmatch(r"[A-Z][A-Z0-9_]*", key):
            errors.add(f"{path}:{number}: invalid variable name {key!r}")
            continue
        if key in values:
            errors.add(f"{path}:{number}: duplicate variable {key}")
            continue
        if value and value[0:1] in {'"', "'"}:
            try:
                parsed = shlex.split(value, posix=True)
            except ValueError as exc:
                errors.add(f"{path}:{number}: invalid quoted value: {exc}")
                continue
            if len(parsed) != 1:
                errors.add(f"{path}:{number}: values must not contain shell commands")
                continue
            value = parsed[0]
        values[key] = value
    return values


def load_yaml(path: Path, errors: ValidationErrors) -> Any:
    try:
        with path.open("r", encoding="utf-8") as handle:
            return yaml.safe_load(handle)
    except (OSError, yaml.YAMLError) as exc:
        errors.add(f"YAML parse failed for {path}: {exc}")
        return None


def validate_yaml_files(root: Path, errors: ValidationErrors) -> None:
    patterns = (
        "salig/**/*.yaml",
        "salig/**/*.yml",
        "deploy/qnap/**/*.yaml",
        "deploy/qnap/**/*.yml",
        ".github/workflows/salig-*.yaml",
        ".github/workflows/salig-*.yml",
    )
    paths = sorted({path for pattern in patterns for path in root.glob(pattern) if path.is_file()})
    errors.require(bool(paths), "no SALIG YAML files were found")
    for path in paths:
        load_yaml(path, errors)


def _normalise_environment(value: Any) -> dict[str, str]:
    if isinstance(value, Mapping):
        return {str(key): str(item) for key, item in value.items()}
    result: dict[str, str] = {}
    if isinstance(value, Sequence) and not isinstance(value, (str, bytes)):
        for item in value:
            if isinstance(item, str) and "=" in item:
                key, raw = item.split("=", 1)
                result[key] = raw
    return result


def _normalise_volumes(value: Any) -> list[str]:
    if not isinstance(value, Sequence) or isinstance(value, (str, bytes)):
        return []
    result: list[str] = []
    for item in value:
        if isinstance(item, str):
            result.append(item)
        elif isinstance(item, Mapping):
            source = item.get("source", "")
            target = item.get("target", "")
            mode = "ro" if item.get("read_only") else "rw"
            result.append(f"{source}:{target}:{mode}")
    return result


def _volume_is_read_only(volumes: Iterable[str], target: str) -> bool:
    for volume in volumes:
        parts = volume.rsplit(":", 2)
        if len(parts) >= 2 and parts[-2] == target and parts[-1] == "ro":
            return True
        if len(parts) == 2 and parts[1] == target:
            return False
    return False


