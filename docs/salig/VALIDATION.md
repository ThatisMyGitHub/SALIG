# SALIG Repository Validation

## Purpose

The SALIG validation suite enforces repository and deployment-policy invariants before runtime inference work begins. It is static validation only: passing it does not approve an image, backend, model, operation, QNAP host, or production deployment.

The suite has two profiles:

- `baseline` validates the current deny-by-default repository. Empty production artifact pins and an empty model allowlist are permitted because nothing is approved yet.
- `accepted-deployment` adds promotion gates. It rejects empty or placeholder artifact pins, requires an external deployment environment file with a digest-pinned image, and requires every allowlisted model to be approved.

The profiles intentionally preserve the distinction between a safe repository scaffold and an accepted deployment.

## Local use

From the repository root, install the pinned Python dependencies:

```bash
python3 -m pip install -r scripts/requirements-salig-validation.txt
```

Run the baseline checks:

```bash
scripts/salig-validate.sh --profile baseline
```

When Docker Compose is available, require a complete Compose render as CI does:

```bash
scripts/salig-validate.sh --profile baseline --require-compose
```

Run the regression tests:

```bash
python3 -m unittest discover -s tests/salig-validation -p 'test_*.py' -v
```

For a future accepted deployment, keep the real environment file outside Git and run:

```bash
scripts/salig-validate.sh \
  --profile accepted-deployment \
  --deployment-env /protected/path/to/salig.env \
  --require-compose \
  --require-git-governance
```

The accepted-deployment profile reads production artifact pins from `salig/baseline.env`. A different reviewed evidence file can be supplied with `--baseline-file`.

## CI behavior

`.github/workflows/salig-validation.yml` runs on every pull request targeting `salig/integration`, on pushes to that branch, and by manual dispatch.

The workflow:

- has read-only repository permission;
- uses a GitHub-hosted runner;
- pins `actions/checkout` to an immutable commit;
- does not use repository or production secrets;
- does not pull models or execute inference;
- renders Compose without starting containers;
- validates that `master` still equals the recorded upstream baseline;
- runs the policy regression tests.

The status check name is:

```text
SALIG validation / policy
```

After the pull request is reviewed and merged, this check can be made required by the `SALIG integration protection` ruleset.

## Requirement mapping

| Milestone requirement | Enforced by |
|---|---|
| QNAP Compose syntax | `docker compose config` with `.env.example` in required-Compose mode |
| No host `ports:` exposure | structural Compose check |
| Digest-pinned production image | accepted-deployment environment validation |
| No empty or placeholder accepted pins | accepted-deployment baseline and environment validation |
| Model allowlist schema | `salig/model-allowlist.schema.json` plus Draft 2020-12 validation |
| Duplicate model IDs | case-insensitive uniqueness of model `alias` values |
| Missing model hashes | required lowercase 64-character SHA-256 |
| Unapproved production models | accepted-deployment profile requires `status: approved` |
| No committed secrets or private keys | targeted SALIG path scan for private-key markers and common token formats |
| `.env` ignored | tracked-file rejection plus `git check-ignore deploy/qnap/.env` |
| No Docker socket | Compose volume inspection |
| No MariaDB credential variables | SALIG deployment-file variable scan |
| Agents disabled | exact Compose environment check |
| MCP disabled | exact Compose environment check |
| Read-only model and configuration mounts | Compose volume-mode inspection |
| Expected internal network | service attachment, external-network and default-name checks |
| Shell syntax | `sh -n` or `bash -n` according to the shebang |
| YAML parsing | PyYAML parse of SALIG-owned YAML files |
| Baseline field syntax | repository, branch, commit, date and digest validation |
| `master` unchanged | CI comparison of `master`, merge base and `SALIG_UPSTREAM_COMMIT` |

The current allowlist uses `alias` as the stable model identifier. A future governance change may introduce a separate `id`, but that must be a reviewed schema migration rather than an implicit reinterpretation.

## Limits

The targeted secret scan protects SALIG-owned paths and avoids claiming that it can retrospectively certify the entire upstream LocalAI history. It is defence in depth, not a replacement for organization-wide secret scanning, image vulnerability analysis, SBOM review, signature verification, or manual security review.

YAML and JSON Schema validity do not prove that a pinned LocalAI version supports a configuration. Exact runtime compatibility remains part of image, backend, model, hardware and synthetic proof-of-concept review.

A green validation check is not production approval.

## Rollback

This milestone adds repository-only files and one documentation link. Rollback is the revert of its feature commit or pull request. No QNAP service, persistent data, secret, model, backend, image, database, or network is changed by the validation suite.
