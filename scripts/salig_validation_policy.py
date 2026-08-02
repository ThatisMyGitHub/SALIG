"""Compose, allowlist, and artifact-pin validation."""
from __future__ import annotations

import datetime as dt
import json
from pathlib import Path
import re
from typing import Any, Mapping

from jsonschema import Draft202012Validator, FormatChecker

from salig_validation_common import (
    BRANCH_NAME, DB_CREDENTIAL_NAME, HEX40, HEX64, IMAGE_WITH_DIGEST,
    PLACEHOLDER, REPOSITORY_NAME, ValidationErrors, load_yaml, parse_env_file,
    _normalise_environment, _normalise_volumes, _volume_is_read_only,
)

def validate_compose_data(compose: Any, errors: ValidationErrors) -> None:
    if not isinstance(compose, Mapping):
        errors.add("deploy/qnap/compose.yaml must contain a YAML mapping")
        return
    services = compose.get("services")
    if not isinstance(services, Mapping) or "localai" not in services:
        errors.add("compose must define services.localai")
        return
    localai = services["localai"]
    if not isinstance(localai, Mapping):
        errors.add("services.localai must be a mapping")
        return

    errors.require("ports" not in localai, "LocalAI service must not define host ports")
    image = localai.get("image")
    errors.require(
        isinstance(image, str) and "${SALIG_LOCALAI_IMAGE:" in image,
        "LocalAI image must be supplied through required SALIG_LOCALAI_IMAGE substitution",
    )
    errors.require(localai.get("privileged") is not True, "LocalAI service must not be privileged")

    cap_drop = localai.get("cap_drop", [])
    errors.require(isinstance(cap_drop, list) and "ALL" in cap_drop, "LocalAI service must drop all Linux capabilities")
    security_opt = localai.get("security_opt", [])
    errors.require(
        isinstance(security_opt, list) and any(str(item).startswith("no-new-privileges") for item in security_opt),
        "LocalAI service must enable no-new-privileges",
    )

    environment = _normalise_environment(localai.get("environment"))
    errors.require(environment.get("LOCALAI_DISABLE_AGENTS", "").lower() == "true", "agents must remain disabled")
    errors.require(environment.get("LOCALAI_DISABLE_MCP", "").lower() == "true", "MCP must remain disabled")

    volumes = _normalise_volumes(localai.get("volumes"))
    errors.require(_volume_is_read_only(volumes, "/models"), "the /models mount must be read-only")
    errors.require(_volume_is_read_only(volumes, "/configuration"), "the /configuration mount must be read-only")
    for volume in volumes:
        lowered = volume.lower()
        if "docker.sock" in lowered or "container-station" in lowered or "/var/run/docker" in lowered:
            errors.add(f"prohibited container-control socket mount: {volume}")

    service_networks = localai.get("networks", {})
    attached = set(service_networks.keys()) if isinstance(service_networks, Mapping) else set(service_networks or [])
    errors.require("salutapp-internal" in attached, "LocalAI must use the SalutApp internal network")
    errors.require("salig-internal" in attached, "LocalAI must use the private SALIG internal network")

    networks = compose.get("networks", {})
    salutapp_network = networks.get("salutapp-internal", {}) if isinstance(networks, Mapping) else {}
    errors.require(
        isinstance(salutapp_network, Mapping) and salutapp_network.get("external") is True,
        "salutapp-internal must be an external network",
    )
    network_name = salutapp_network.get("name") if isinstance(salutapp_network, Mapping) else None
    errors.require(
        isinstance(network_name, str)
        and "SALUTAPP_INTERNAL_NETWORK" in network_name
        and "salutapp-app-internal" in network_name,
        "the external network must default to salutapp-app-internal through SALUTAPP_INTERNAL_NETWORK",
    )


def validate_compose_file(root: Path, errors: ValidationErrors) -> None:
    path = root / "deploy/qnap/compose.yaml"
    compose = load_yaml(path, errors)
    if compose is not None:
        validate_compose_data(compose, errors)

    for candidate in (root / "deploy/qnap").rglob("*"):
        if not candidate.is_file() or candidate.suffix.lower() not in {".yaml", ".yml", ".example"}:
            continue
        text = candidate.read_text(encoding="utf-8", errors="replace")
        if DB_CREDENTIAL_NAME.search(text):
            errors.add(f"database credential variable found in SALIG deployment file: {candidate.relative_to(root)}")


def validate_allowlist_data(
    data: Any,
    schema: Mapping[str, Any],
    errors: ValidationErrors,
    profile: str,
) -> None:
    validator = Draft202012Validator(schema, format_checker=FormatChecker())
    for issue in sorted(validator.iter_errors(data), key=lambda item: list(item.absolute_path)):
        location = ".".join(str(part) for part in issue.absolute_path) or "<root>"
        errors.add(f"model allowlist schema error at {location}: {issue.message}")

    if not isinstance(data, Mapping):
        return
    models = data.get("models")
    if not isinstance(models, list):
        return

    seen: dict[str, int] = {}
    for index, model in enumerate(models):
        if not isinstance(model, Mapping):
            continue
        alias = model.get("alias")
        if isinstance(alias, str):
            folded = alias.casefold()
            if folded in seen:
                errors.add(f"duplicate model alias {alias!r} at indexes {seen[folded]} and {index}")
            else:
                seen[folded] = index
        digest = model.get("sha256")
        if not isinstance(digest, str) or not HEX64.fullmatch(digest):
            errors.add(f"model entry {index} has no valid lowercase SHA-256")

    if profile == "accepted-deployment":
        errors.require(bool(models), "accepted-deployment profile requires at least one approved model")
        for index, model in enumerate(models):
            if not isinstance(model, Mapping) or model.get("status") != "approved":
                errors.add(f"model entry {index} is not approved for accepted deployment")


def validate_allowlist(root: Path, errors: ValidationErrors, profile: str) -> None:
    allowlist_path = root / "salig/model-allowlist.yaml"
    schema_path = root / "salig/model-allowlist.schema.json"
    data = load_yaml(allowlist_path, errors)
    try:
        schema = json.loads(schema_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        errors.add(f"cannot load model allowlist schema: {exc}")
        return
    if data is not None:
        validate_allowlist_data(data, schema, errors, profile)


def _is_non_placeholder(value: str) -> bool:
    return bool(value) and not PLACEHOLDER.search(value)


def _valid_digest(value: str) -> bool:
    return bool(HEX64.fullmatch(value) or re.fullmatch(r"sha256:[0-9a-f]{64}", value))


def validate_baseline_values(values: Mapping[str, str], errors: ValidationErrors, profile: str) -> None:
    required_source = {
        "SALIG_UPSTREAM_REPOSITORY",
        "SALIG_FORK_REPOSITORY",
        "SALIG_UPSTREAM_BRANCH",
        "SALIG_INTEGRATION_BRANCH",
        "SALIG_UPSTREAM_COMMIT",
        "SALIG_BASELINE_RECORDED_AT",
    }
    missing = sorted(key for key in required_source if not values.get(key))
    for key in missing:
        errors.add(f"baseline is missing required source field {key}")

    for key in ("SALIG_UPSTREAM_REPOSITORY", "SALIG_FORK_REPOSITORY"):
        value = values.get(key, "")
        errors.require(bool(REPOSITORY_NAME.fullmatch(value)), f"{key} must be owner/repository")
    for key in ("SALIG_UPSTREAM_BRANCH", "SALIG_INTEGRATION_BRANCH"):
        value = values.get(key, "")
        errors.require(bool(BRANCH_NAME.fullmatch(value)), f"{key} is not a syntactically valid branch name")
    errors.require(bool(HEX40.fullmatch(values.get("SALIG_UPSTREAM_COMMIT", ""))), "SALIG_UPSTREAM_COMMIT must be 40 lowercase hexadecimal characters")
    try:
        dt.date.fromisoformat(values.get("SALIG_BASELINE_RECORDED_AT", ""))
    except ValueError:
        errors.add("SALIG_BASELINE_RECORDED_AT must use YYYY-MM-DD")

    artifact_fields = (
        "SALIG_LOCALAI_IMAGE",
        "SALIG_LOCALAI_IMAGE_DIGEST",
        "SALIG_BACKEND_NAME",
        "SALIG_BACKEND_DIGEST",
        "SALIG_MODEL_ALIAS",
        "SALIG_MODEL_SHA256",
        "SALIG_CONFIGURATION_SHA256",
    )
    for key in artifact_fields:
        if key not in values:
            errors.add(f"baseline is missing artifact field {key}")

    if profile == "accepted-deployment":
        for key in artifact_fields:
            value = values.get(key, "")
            errors.require(_is_non_placeholder(value), f"accepted-deployment profile requires a non-placeholder {key}")
        errors.require(_valid_digest(values.get("SALIG_LOCALAI_IMAGE_DIGEST", "")), "SALIG_LOCALAI_IMAGE_DIGEST must be a SHA-256 digest")
        errors.require(_valid_digest(values.get("SALIG_BACKEND_DIGEST", "")), "SALIG_BACKEND_DIGEST must be a SHA-256 digest")
        errors.require(bool(HEX64.fullmatch(values.get("SALIG_MODEL_SHA256", ""))), "SALIG_MODEL_SHA256 must be 64 lowercase hexadecimal characters")
        errors.require(bool(HEX64.fullmatch(values.get("SALIG_CONFIGURATION_SHA256", ""))), "SALIG_CONFIGURATION_SHA256 must be 64 lowercase hexadecimal characters")
        image_name = values.get("SALIG_LOCALAI_IMAGE", "")
        errors.require("latest" not in image_name.lower() and ":master" not in image_name.lower(), "SALIG_LOCALAI_IMAGE must not identify a floating tag")


def validate_deployment_env(values: Mapping[str, str], errors: ValidationErrors) -> None:
    required = ("SALIG_LOCALAI_IMAGE", "SALIG_API_KEY", "SALIG_DATA_ROOT", "SALUTAPP_INTERNAL_NETWORK")
    for key in required:
        errors.require(_is_non_placeholder(values.get(key, "")), f"deployment environment requires non-placeholder {key}")
    errors.require(bool(IMAGE_WITH_DIGEST.fullmatch(values.get("SALIG_LOCALAI_IMAGE", ""))), "deployment SALIG_LOCALAI_IMAGE must be repository@sha256:<64 lowercase hex>")
    errors.require(len(values.get("SALIG_API_KEY", "")) >= 32, "SALIG_API_KEY must contain at least 32 characters")
    errors.require(values.get("SALUTAPP_INTERNAL_NETWORK") == "salutapp-app-internal", "accepted deployment must use the approved salutapp-app-internal network")


def validate_pins(
    root: Path,
    errors: ValidationErrors,
    profile: str,
    baseline_file: Path | None,
    deployment_env: Path | None,
) -> Mapping[str, str]:
    baseline_path = baseline_file or (root / "salig/baseline.env")
    baseline_values = parse_env_file(baseline_path, errors)
    validate_baseline_values(baseline_values, errors, profile)
    if profile == "accepted-deployment":
        if deployment_env is None:
            errors.add("accepted-deployment profile requires --deployment-env")
        else:
            deployment_values = parse_env_file(deployment_env, errors)
            validate_deployment_env(deployment_values, errors)
    return baseline_values


