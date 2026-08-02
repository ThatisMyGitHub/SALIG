# SALIG — SalutApp Local Inference Gateway

SALIG is the controlled on-premise inference boundary through which SalutApp may delegate explicitly approved model operations.

This branch is intentionally separate from the upstream-derived `master` branch:

- `master` remains an unmodified mirror used to inspect and adopt reviewed LocalAI upstream changes.
- `salig/integration` contains SalutApp-specific policy, architecture, deployment and integration work.
- Feature work must be developed on short-lived branches and merged into `salig/integration` through reviewed pull requests.
- No SALIG-specific commit should be pushed to `master`.

## Current scope

The initial scope is deliberately narrow:

1. Local text generation using an approved, pinned model.
2. Structured extraction from content explicitly selected by SalutApp.
3. Summarisation of an explicitly selected, minimum-necessary payload.
4. Embedding generation for an application-curated knowledge collection.

SALIG is not a generic chatbot over health records. It must not autonomously select records, query the SalutApp database, invoke tools, mutate application data, or route protected data to external providers.

## Repository map

- `docs/salig/ARCHITECTURE.md` — system boundaries, components and data flow.
- `docs/salig/SECURITY_POLICY.md` — mandatory security and model-governance controls.
- `docs/salig/UPSTREAM_BASELINE.md` — exact LocalAI baseline and update process.
- `docs/salig/VALIDATION.md` — local and CI policy validation profiles and controls.
- `salig/baseline.env` — machine-readable upstream pin.
- `salig/model-allowlist.yaml` — deny-by-default model approval registry.
- `deploy/qnap/` — QNAP Container Station deployment scaffold.
- `deploy/qnap/hardware-discovery/` — read-only host discovery, evidence verification and route-decision package prepared for execution when platform access becomes available.

## Status

This branch establishes the integration baseline only. It does not approve a production image, backend or model. Production activation requires completed hardware discovery, image digest selection, model checksum approval, threat review, isolated validation and explicit operational acceptance.
