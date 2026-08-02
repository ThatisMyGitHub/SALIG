#!/usr/bin/env python3
"""Static policy validation for SALIG-owned repository content."""
from __future__ import annotations

import argparse
from pathlib import Path
import sys
from typing import Sequence

from salig_validation_common import ValidationErrors, validate_yaml_files
from salig_validation_policy import (
    validate_allowlist, validate_allowlist_data, validate_baseline_values,
    validate_compose_data, validate_compose_file, validate_deployment_env,
    validate_pins,
)
from salig_validation_repo import (
    validate_compose_render, validate_git_governance,
    validate_repository_hygiene, validate_shell_scripts,
)

def run_validation(
    root: Path,
    profile: str = "baseline",
    baseline_file: Path | None = None,
    deployment_env: Path | None = None,
    require_compose: bool = False,
    require_git_governance: bool = False,
) -> list[str]:
    errors = ValidationErrors()
    validate_yaml_files(root, errors)
    validate_compose_file(root, errors)
    validate_allowlist(root, errors, profile)
    baseline_values = validate_pins(root, errors, profile, baseline_file, deployment_env)
    validate_repository_hygiene(root, errors)
    validate_shell_scripts(root, errors)
    validate_compose_render(root, errors, require_compose)
    validate_git_governance(root, baseline_values, errors, require_git_governance)
    return errors.items


def parse_args(argv: Sequence[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument("--profile", choices=("baseline", "accepted-deployment"), default="baseline")
    parser.add_argument("--baseline-file", type=Path)
    parser.add_argument("--deployment-env", type=Path)
    parser.add_argument("--require-compose", action="store_true")
    parser.add_argument("--require-git-governance", action="store_true")
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> int:
    args = parse_args(argv or sys.argv[1:])
    root = args.root.resolve()
    failures = run_validation(
        root=root,
        profile=args.profile,
        baseline_file=args.baseline_file.resolve() if args.baseline_file else None,
        deployment_env=args.deployment_env.resolve() if args.deployment_env else None,
        require_compose=args.require_compose,
        require_git_governance=args.require_git_governance,
    )
    if failures:
        for failure in failures:
            print(f"ERROR: {failure}", file=sys.stderr)
        print(f"SALIG validation failed with {len(failures)} error(s).", file=sys.stderr)
        return 1
    print(f"SALIG {args.profile} validation passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
