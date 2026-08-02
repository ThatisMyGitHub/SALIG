"""Repository hygiene, shell, Compose render, and Git-governance checks."""
from __future__ import annotations

from pathlib import Path
import shutil
import subprocess
import tempfile
from typing import Mapping, Sequence

from salig_validation_common import (
    PRIVATE_KEY_MARKER, SALIG_EXACT_PATHS, SALIG_PATH_PREFIXES,
    SECRET_TOKEN_PATTERNS, ValidationErrors,
)

def _git_files(root: Path) -> list[Path]:
    completed = subprocess.run(
        ["git", "-C", str(root), "ls-files", "-z"],
        check=False,
        capture_output=True,
    )
    if completed.returncode != 0:
        return []
    return [root / raw.decode("utf-8") for raw in completed.stdout.split(b"\0") if raw]


def _is_salig_owned(relative: str) -> bool:
    return relative in SALIG_EXACT_PATHS or relative.startswith(SALIG_PATH_PREFIXES)


def validate_repository_hygiene(root: Path, errors: ValidationErrors) -> None:
    tracked = _git_files(root)
    if not tracked:
        errors.add("Git tracked-file inventory is unavailable")
        return

    for path in tracked:
        relative = path.relative_to(root).as_posix()
        if not _is_salig_owned(relative):
            continue
        name = path.name
        if name == ".env" or (name.startswith(".env.") and not name.endswith(".example")):
            errors.add(f"tracked environment file is prohibited: {relative}")
        if path.suffix.lower() in {".pem", ".key", ".p12", ".pfx"}:
            errors.add(f"tracked private-key or certificate bundle is prohibited: {relative}")
        if not path.is_file() or path.stat().st_size > 2_000_000:
            continue
        text = path.read_text(encoding="utf-8", errors="ignore")
        if PRIVATE_KEY_MARKER.search(text):
            errors.add(f"private key material detected in {relative}")
        for pattern in SECRET_TOKEN_PATTERNS:
            if pattern.search(text):
                errors.add(f"probable secret token detected in {relative}")
                break

    ignored = subprocess.run(
        ["git", "-C", str(root), "check-ignore", "-q", "deploy/qnap/.env"],
        check=False,
    )
    errors.require(ignored.returncode == 0, "deploy/qnap/.env must be ignored by Git")


def validate_shell_scripts(root: Path, errors: ValidationErrors) -> None:
    scripts = [path for path in _git_files(root) if path.suffix == ".sh" and _is_salig_owned(path.relative_to(root).as_posix())]
    errors.require(bool(scripts), "no SALIG shell scripts were found")
    for path in scripts:
        first_line = path.read_text(encoding="utf-8", errors="replace").splitlines()[:1]
        interpreter = "bash" if first_line and "bash" in first_line[0] else "sh"
        completed = subprocess.run([interpreter, "-n", str(path)], check=False, capture_output=True, text=True)
        if completed.returncode != 0:
            errors.add(f"shell syntax failed for {path.relative_to(root)}: {completed.stderr.strip()}")


def validate_compose_render(root: Path, errors: ValidationErrors, required: bool) -> None:
    docker = subprocess.run(["sh", "-c", "command -v docker"], check=False, capture_output=True, text=True)
    if docker.returncode != 0:
        if required:
            errors.add("docker is required to render the QNAP Compose file")
        return

    source = root / "deploy/qnap"
    with tempfile.TemporaryDirectory(prefix="salig-compose-") as temporary:
        deploy = Path(temporary)
        shutil.copy2(source / "compose.yaml", deploy / "compose.yaml")
        (deploy / "configuration").mkdir()
        (deploy / ".env").write_text(
            "\n".join(
                (
                    "SALIG_LOCALAI_IMAGE=registry.invalid/salig/localai@sha256:" + "0" * 64,
                    "SALIG_API_KEY=synthetic-compose-validation-key-0000000000000000",
                    "SALIG_DATA_ROOT=/srv/salig-validation",
                    "SALUTAPP_INTERNAL_NETWORK=salutapp-app-internal",
                    "SALIG_CPU_LIMIT=4.0",
                    "SALIG_MEMORY_LIMIT=12g",
                    "SALIG_PIDS_LIMIT=512",
                    "SALIG_TMPFS_SIZE=1g",
                    "",
                )
            ),
            encoding="utf-8",
        )
        completed = subprocess.run(
            [
                "docker",
                "compose",
                "--project-directory",
                str(deploy),
                "--env-file",
                str(deploy / ".env"),
                "-f",
                str(deploy / "compose.yaml"),
                "config",
            ],
            check=False,
            capture_output=True,
            text=True,
        )
    if completed.returncode != 0:
        errors.add(f"Docker Compose render failed: {completed.stderr.strip()}")


def _resolve_git_ref(root: Path, candidates: Sequence[str]) -> str | None:
    for candidate in candidates:
        completed = subprocess.run(
            ["git", "-C", str(root), "rev-parse", "--verify", candidate],
            check=False,
            capture_output=True,
            text=True,
        )
        if completed.returncode == 0:
            return completed.stdout.strip()
    return None


def validate_git_governance(
    root: Path,
    baseline_values: Mapping[str, str],
    errors: ValidationErrors,
    required: bool,
) -> None:
    if not required:
        return
    expected = baseline_values.get("SALIG_UPSTREAM_COMMIT", "")
    master_sha = _resolve_git_ref(root, ("refs/remotes/origin/master", "refs/heads/master"))
    if master_sha is None:
        errors.add("master ref is unavailable; fetch origin/master before governance validation")
        return
    errors.require(master_sha == expected, f"master moved from the recorded upstream baseline: expected {expected}, found {master_sha}")
    completed = subprocess.run(
        ["git", "-C", str(root), "merge-base", master_sha, "HEAD"],
        check=False,
        capture_output=True,
        text=True,
    )
    if completed.returncode != 0:
        errors.add("cannot compute merge base between master and current HEAD")
        return
    errors.require(completed.stdout.strip() == expected, "current SALIG work is not rooted at the recorded upstream baseline")


