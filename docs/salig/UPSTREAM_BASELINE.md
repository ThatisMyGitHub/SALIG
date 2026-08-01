# SALIG Upstream Baseline

## Initial baseline

| Field | Value |
|---|---|
| Upstream project | `mudler/LocalAI` |
| SALIG fork | `ThatisMyGitHub/SALIG` |
| Upstream-derived branch | `master` |
| SALIG integration branch | `salig/integration` |
| Baseline commit | `cedcbf97a9df97a52aa0422902c1404b84fedb03` |
| Baseline commit date | `2026-08-01T07:26:23Z` |
| Baseline commit subject | `fix(llama-cpp): retain CPU variants in GPU builds (#11255)` |
| Baseline recorded | `2026-08-01` |

The `salig/integration` branch was created directly from the baseline commit above. All initial SALIG-specific files are descendants of that exact commit.

## Meaning of the pin

This source pin records the code baseline from which SALIG integration work began. It does not by itself approve:

- a LocalAI release;
- a container image;
- an OCI backend image;
- a model file;
- a production deployment.

Production approval requires separate immutable pins for the deployed image, backend and model artifacts.

## Branch responsibilities

### `master`

`master` is reserved for upstream history. It may be updated only by synchronizing reviewed commits from `mudler/LocalAI`. SALIG-specific policy, deployment or application integration changes must not be committed to it.

### `salig/integration`

`salig/integration` is the long-lived SALIG integration target. It contains the controlled delta from upstream and is the base branch for SALIG feature work.

### Feature branches

Use short-lived branches such as:

- `salig/feature/gateway-contract`
- `salig/feature/qnap-poc`
- `salig/security/image-verification`
- `salig/upstream/<version-or-date>`

Feature branches must merge into `salig/integration`, not into `master`.

## Upstream update procedure

1. Identify the exact upstream tag or commit proposed for adoption.
2. Review release notes, changed dependencies, backend changes, open regressions and security implications.
3. Fast-forward or synchronize the fork's `master` branch without SALIG-specific commits.
4. Create `salig/upstream/<version-or-date>` from the current `salig/integration` branch.
5. Merge or rebase the exact reviewed upstream commit into that update branch.
6. Resolve conflicts without weakening SALIG controls.
7. Update this file and `salig/baseline.env` with the proposed upstream commit.
8. Rebuild or select a pinned image and record its digest.
9. Re-run functional, authorization, resource, logging, upgrade and rollback tests.
10. Merge the update branch into `salig/integration` only after review and acceptance.

Do not automatically merge upstream changes into the deployed SALIG environment.

## Production artifact record

For each promoted build, record at minimum:

```text
SALIG source commit:
LocalAI upstream commit:
Container image repository:
Container image digest:
Backend name and digest/checksum:
Model alias:
Model source:
Model filename:
Model SHA-256:
Model license:
Configuration checksum:
Target environment:
Approval date:
Rollback image digest:
Rollback source commit:
```

## Verification commands

After cloning the fork locally, the source relationship can be checked with:

```bash
git rev-parse master
git merge-base master salig/integration
git log --oneline --decorate --graph master..salig/integration
```

The merge base for the initial integration branch must resolve to:

```text
cedcbf97a9df97a52aa0422902c1404b84fedb03
```

Any unexpected SALIG-specific commit on `master` must be investigated before further synchronization.