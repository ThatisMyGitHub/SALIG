# SALIG Security Policy

## 1. Policy statement

SALIG is a deny-by-default inference service. No model, backend, operation, caller, data class or network path is permitted merely because LocalAI supports it. Every production capability requires explicit approval and a reproducible pin.

The controls in this document are mandatory for any SalutApp deployment handling real user or health-related data.

## 2. Data-handling principles

1. SalutApp selects the minimum necessary data before calling SALIG.
2. SALIG must not query SalutApp storage directly.
3. Protected content must remain on infrastructure controlled by SalutApp.
4. Prompt and response bodies must not be written to ordinary application, proxy or container logs.
5. Temporary content must be bounded and removed after processing.
6. Model output is untrusted and must be validated by the SalutApp AI Gateway.
7. No model output may directly mutate a health record.
8. Inference must fail closed when authorization, operation policy, model approval or output validation is uncertain.

## 3. Identity and access

### Required

- Only the SalutApp AI Gateway may call the SALIG inference endpoint.
- Browser, mobile and public reverse-proxy access is prohibited.
- The initial gateway credential must be long, random, unique to SALIG and stored outside the repository.
- Production should use a restricted identity mechanism with credential rotation and per-client attribution.
- Administrative interfaces require separate credentials and must not share the inference credential.
- Access failures must be logged without logging request content.

### Prohibited

- shared default credentials;
- credentials committed to Git;
- inference endpoints without authentication;
- direct end-user API keys;
- using a full-administrator key inside the SalutApp web application;
- database credentials inside the SALIG container.

## 4. Network controls

- Do not publish LocalAI port `8080` on a host or public interface.
- Attach SALIG only to the dedicated internal network and the specific shared network required by the SalutApp AI Gateway.
- Deny unrestricted outbound internet access in production.
- Provision images, models and backends through a controlled maintenance process, then run without runtime downloads.
- Do not mount the Docker socket, Container Station socket or host root filesystem.
- A future remote inference node must use an authenticated and encrypted private connection with explicit source restrictions.

## 5. Supply-chain controls

### Container image

- Floating tags such as `latest`, `master` or an unqualified version are prohibited in production.
- The deployed image reference must include an immutable digest.
- The image digest must be reviewed, recorded and tested before promotion.
- A software bill of materials and vulnerability scan should be retained for each approved image.
- Upgrade testing must use a copy of persistent data and include rollback rehearsal.

### Backend

- Only the required backend may be present.
- Runtime backend installation is prohibited in production.
- Backend artifacts must originate from an approved build or signed upstream artifact and be pinned by digest or checksum.
- Agents, MCP, skills and unused modalities must remain disabled.

### Models

- Every model file must have a cryptographic checksum.
- The model license, origin, intended operation, quantization and context limit must be recorded.
- Models are mounted read-only.
- Model aliases exposed to SalutApp must be stable and must not reveal arbitrary file paths.
- An unlisted model is denied even when it exists on disk.

## 6. Operation governance

Each approved operation requires a versioned policy containing:

- operation identifier;
- business purpose;
- approved caller roles;
- approved input fields and data classes;
- approved model alias;
- maximum input bytes and context tokens;
- maximum generated tokens;
- timeout;
- output schema and validation rules;
- human-review requirement;
- persistence and retention rules;
- failure behavior;
- test cases and acceptance owner.

An operation change that expands data access, output authority, model capability or retention is a security-relevant change and requires renewed review.

## 7. Runtime hardening

The production container must use, where compatible with the approved image:

- `no-new-privileges`;
- dropped Linux capabilities;
- explicit CPU and memory limits;
- explicit process limits;
- bounded temporary storage;
- read-only model and configuration mounts;
- a non-public network;
- a restart policy that does not create an uncontrolled crash loop;
- no privileged mode;
- no host PID, IPC or network namespace;
- no device mounts unless separately approved for an accelerator.

Any relaxation must be documented with the technical reason, risk and compensating control.

## 8. Feature restrictions for the initial deployment

The following must remain disabled until a separate approval exists:

- LocalAI agents and agent pools;
- MCP servers, MCP clients and tool execution;
- dynamic skills;
- cloud proxying or cloud model fallback;
- model-gallery installation at runtime;
- arbitrary URL imports;
- fine-tuning and quantization services;
- image and video generation;
- speech, voice and biometric processing;
- peer-to-peer mode;
- distributed workers;
- user-facing LocalAI administration UI;
- direct RAG over the SalutApp database.

## 9. Logging and audit

Permitted operational fields include:

- opaque request ID;
- operation ID and version;
- model alias and approved revision;
- caller service identity;
- start and completion timestamps;
- duration;
- input and output token counts;
- outcome and validation code;
- resource-limit or timeout event.

The following must not appear in routine logs or traces:

- names;
- dates of birth;
- medical details;
- prompts;
- generated responses;
- access tokens;
- API keys;
- model file contents;
- full request payloads.

Debug logging must remain disabled with real data. Any temporary diagnostic capture requires explicit approval, encryption, access restriction, a defined expiry and confirmed deletion.

## 10. Secrets

- Secrets are stored in deployment-specific protected files or a secrets manager, never in Git.
- Example files contain placeholders only.
- Credentials must be rotated after suspected exposure and at defined intervals.
- Backups containing secrets must receive equivalent protection.
- Secrets must not be copied into support bundles, screenshots or issue reports.

## 11. Validation and testing

Before promotion, every approved combination of image, backend, model and operation must pass:

1. checksum and digest verification;
2. configuration validation;
3. synthetic functional tests;
4. authorization-denial tests;
5. request-size, token, timeout and concurrency-limit tests;
6. malformed-output and schema-rejection tests;
7. prompt-injection and instruction-conflict tests appropriate to the operation;
8. logging review confirming protected content is absent;
9. resource-contention testing alongside SalutApp, MariaDB and backups;
10. restart, upgrade and rollback tests.

Healthcare correctness must be evaluated separately from technical availability. A technically valid response is not necessarily clinically or factually correct.

## 12. Change management

- `master` tracks reviewed upstream history and contains no SALIG-specific changes.
- `salig/integration` is the controlled integration target.
- Work is performed on short-lived branches.
- Direct pushes to `salig/integration` are disabled once the repository ruleset is applied.
- Pull requests must show the upstream baseline, changed security assumptions, tests and rollback impact.
- Force pushes and branch deletion are prohibited.
- Emergency bypass use must be documented and followed by review.

## 13. Incident response

On suspected compromise, data leakage or unauthorized model behavior:

1. disable the affected operation at the SalutApp AI Gateway;
2. isolate or stop SALIG without interrupting core SalutApp functions;
3. preserve non-content audit evidence;
4. rotate service and administrative credentials;
5. identify the image, backend, model and configuration revisions involved;
6. assess whether protected content left the approved boundary;
7. restore only from a known approved baseline;
8. document cause, impact, corrective action and prevention.

SALIG must never be a dependency required for ordinary access to health records. Core SalutApp services must remain usable while inference is disabled.