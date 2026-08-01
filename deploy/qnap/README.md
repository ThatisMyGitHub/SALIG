# SALIG QNAP Deployment Scaffold

This directory provides the first controlled QNAP Container Station layout for SALIG. It is a scaffold, not a production-ready deployment. It deliberately refuses to start until an immutable LocalAI image reference and gateway credential are supplied.

## Design properties

- no host port is published;
- only the SalutApp AI Gateway may reach `salig-localai:8080` through the existing internal Docker network;
- models and LocalAI configuration are mounted read-only;
- agents and MCP are disabled;
- CPU, memory, process and temporary-storage limits are explicit;
- the LocalAI image must be pinned by digest;
- no model is approved by the repository's initial allowlist;
- no MariaDB credentials or direct database connection are present.

## Directory layout

Recommended QNAP host layout:

```text
/share/data/dockerapps/salig/
├── data/                 # bounded LocalAI runtime data
├── models/               # approved model files, mounted read-only
├── manifests/            # local checksums and approval records
└── backups/              # controlled configuration backups, if required
```

Repository-controlled deployment files:

```text
deploy/qnap/
├── compose.yaml
├── .env.example
├── configuration/
└── scripts/
```

Do not put secrets, model files or protected application data in the Git repository.

## Prerequisites

Before starting a container:

1. Record the QNAP model, CPU, CPU instruction set, RAM, storage type, free capacity and Container Station version.
2. Confirm that the existing `salutapp-app-internal` Docker network is present, or set `SALUTAPP_INTERNAL_NETWORK` to the approved replacement.
3. Select a LocalAI image suitable for the verified QNAP architecture.
4. Pull the candidate image during a controlled maintenance step.
5. Resolve and record its immutable repository digest.
6. Review the image and its included or required backend.
7. Select a small model for synthetic testing only.
8. Verify the model license and SHA-256 checksum.
9. Add the model to `salig/model-allowlist.yaml` through a reviewed pull request before any accepted deployment.
10. Ensure SalutApp, MariaDB, backups and storage operations retain resource priority.

## Preparing the environment

From this directory:

```bash
cp .env.example .env
```

Edit `.env` and replace every placeholder. Generate the gateway-only key with a secure local command such as:

```bash
openssl rand -base64 48
```

Create the persistent directories on QNAP:

```bash
mkdir -p \
  /share/data/dockerapps/salig/data \
  /share/data/dockerapps/salig/models \
  /share/data/dockerapps/salig/manifests \
  /share/data/dockerapps/salig/backups
```

Copy only approved model files into `models/`, then create and retain a checksum record:

```bash
sha256sum /share/data/dockerapps/salig/models/* \
  > /share/data/dockerapps/salig/manifests/models.sha256
```

Review file ownership and permissions so the container can read models without granting broad host access.

## Pinning the image

A floating tag may be pulled for evaluation, but it must not remain in `.env`. After pulling a reviewed candidate, resolve its digest locally:

```bash
docker pull <candidate-image:tag>
docker inspect --format='{{index .RepoDigests 0}}' <candidate-image:tag>
```

Copy the returned `repository@sha256:...` value into `SALIG_LOCALAI_IMAGE` and record it in the release evidence. The same digest must be used for rollback rehearsal and deployment approval.

## Preflight validation

Run the repository preflight script:

```bash
bash scripts/preflight.sh
```

It checks required values, rejects a non-digest image reference, checks persistent directories and the shared network, and renders the Compose configuration without starting a container.

Also inspect the rendered configuration manually:

```bash
docker compose --env-file .env -f compose.yaml config
```

Confirm that:

- there is no `ports:` mapping;
- the image contains `@sha256:`;
- the model mount is read-only;
- the correct external network is selected;
- agents and MCP remain disabled;
- resource limits match the approved test envelope;
- no secret is shown in screenshots or copied into an issue.

## Starting the synthetic proof of concept

Do not use real SalutApp records in the first run.

```bash
docker compose --env-file .env -f compose.yaml up -d
```

Inspect only non-content operational logs:

```bash
docker compose --env-file .env -f compose.yaml ps
docker compose --env-file .env -f compose.yaml logs --tail=100 localai
```

Because no host port is published, validation must be performed from a temporary approved container on the shared internal network or through the future SalutApp AI Gateway. Do not add a public or LAN port merely for convenience.

## Configuration and model loading

The Compose file mounts `configuration/` read-only at `/configuration` and the approved host model directory read-only at `/models`.

The initial repository contains no active model configuration. Add a reviewed LocalAI model configuration only after confirming the schema supported by the exact pinned image. The configuration must reference a file already present in `/models`; it must not instruct LocalAI to download a model or backend at runtime.

The scaffold maps the gateway secret to LocalAI's `API_KEY` setting and sets `LOCALAI_DISABLE_AGENTS=true` and `LOCALAI_DISABLE_MCP=true`. These settings must be revalidated whenever the pinned upstream or image baseline changes.

## Resource validation

Begin with:

- one small text model;
- concurrency one;
- context between 4K and 8K only if memory tests permit;
- no embedding model unless the test explicitly requires it;
- no GPU or host-device mapping;
- synthetic payloads;
- normal SalutApp, MariaDB and backup workloads running during contention tests.

Stop the proof of concept if it causes swapping, storage latency, database degradation, backup disruption, thermal instability or repeated container restarts.

## Shutdown and rollback

Stop the service without deleting persistent data:

```bash
docker compose --env-file .env -f compose.yaml down
```

Rollback consists of restoring the previously approved:

- source commit;
- image digest;
- configuration checksum;
- model checksum;
- environment settings.

Do not use `docker compose down -v` in this layout. The deployment uses host bind mounts, but destructive commands should still be treated as unsafe until paths are verified.

## Production acceptance gate

Production activation remains blocked until all of the following exist:

- verified QNAP hardware inventory;
- approved operation contract in the SalutApp AI Gateway;
- digest-pinned image and backend evidence;
- approved model allowlist entry and checksum;
- authorization-denial tests;
- output schema validation;
- logging review showing no protected content;
- contention and stability results;
- backup and rollback evidence;
- branch protection on `salig/integration`;
- explicit operational acceptance.
