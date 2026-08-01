# SALIG Architecture

## 1. Purpose

SALIG provides a local, policy-controlled inference execution plane for SalutApp. It is not the owner of user identity, healthcare authorization, consent, record selection or clinical meaning. Those responsibilities remain in SalutApp.

The design separates application policy from model execution:

```text
SalutApp user and RBAC
        |
        v
SalutApp AI Gateway
- authenticates the caller
- evaluates the operation allowlist
- selects the minimum necessary data
- removes unsupported fields
- records provenance and audit metadata
- validates the response schema
        |
        v
SALIG internal API
- accepts only gateway-originated requests
- resolves an approved model alias
- enforces resource and request limits
- executes the pinned LocalAI backend
        |
        v
Approved local model and backend
```

## 2. Trust boundaries

### 2.1 SalutApp boundary

SalutApp remains authoritative for:

- user identity and role-based access control;
- parent, guardian and child-record authorization;
- consent and purpose limitation;
- selection of records and fields;
- event ownership and tenancy constraints;
- the distinction between clinical, administrative and technical content;
- response validation before anything is shown or stored;
- all writes to the SalutApp database;
- audit linkage between a user action and an inference request.

### 2.2 SALIG boundary

SALIG is responsible for:

- exposing a private inference endpoint only to the approved gateway network;
- mapping stable application model aliases to approved model files and configurations;
- refusing unapproved models, modalities and operations;
- enforcing context, token, concurrency, memory and timeout limits;
- preventing runtime model or backend installation in production;
- producing operational telemetry that excludes protected content;
- returning generated content without making application decisions.

### 2.3 Model boundary

A model is an untrusted probabilistic component. Its output must be treated as data, not as authority. A model must never receive:

- database credentials;
- unrestricted filesystem access;
- Docker or Container Station control sockets;
- network credentials;
- direct access to the SalutApp database;
- autonomous tool or MCP access;
- the ability to update health records.

## 3. Initial approved operation classes

The initial gateway contract may support only the following classes after individual approval:

| Operation | Input selected by | Expected output | Persistence |
|---|---|---|---|
| `summarize.selected_text` | SalutApp | bounded summary | not stored by SALIG |
| `extract.structured_fields` | SalutApp | schema-validated JSON | controlled by SalutApp |
| `classify.supported_category` | SalutApp | value from a fixed enum | controlled by SalutApp |
| `embed.curated_document` | SalutApp ingestion job | vector plus source identifier | approved vector store only |
| `generate.internal_draft` | authorized user action | draft text requiring review | never auto-applied |

Every operation must define:

- an operation identifier and version;
- permitted caller roles;
- permitted record and field types;
- maximum input size;
- approved model alias;
- output schema;
- timeout and token ceiling;
- retention rule;
- audit fields;
- human-review requirement.

## 4. Explicitly prohibited flows

The following are denied by design during the initial phases:

- generic conversational access to all child health records;
- autonomous record discovery or retrieval;
- natural-language-to-SQL execution;
- direct LocalAI access from browsers or mobile clients;
- direct LocalAI access to MariaDB;
- external cloud inference for protected SalutApp data;
- agents, tools, skills or MCP execution;
- arbitrary URL fetching;
- dynamic model-gallery downloads in production;
- runtime backend installation in production;
- image, video, biometric or voice processing without a separate approval;
- model output that directly creates, updates or deletes an application record.

## 5. Network topology

### 5.1 Initial QNAP topology

```text
Existing reverse proxy / SalutApp web network
                 |
          SalutApp AI Gateway
                 |
     salutapp-app-internal network
                 |
           salig-localai
                 |
          salig-internal network
```

The LocalAI port is not published on the QNAP host. Only containers attached to the approved shared internal network can reach it.

### 5.2 Later dedicated inference node

When workload or hardware requirements exceed the safe QNAP envelope:

```text
QNAP
- SalutApp
- policy gateway
- approved model registry
- audit metadata
        |
        | mutually authenticated private connection
        v
Dedicated Linux inference host
- SALIG worker
- local NVMe model cache
- GPU runtime
- no SalutApp database credentials
```

The QNAP remains the policy and data owner; the inference node remains a restricted execution worker.

## 6. Data flow

1. A user invokes an approved SalutApp feature.
2. SalutApp authenticates the user and verifies access to each source record.
3. The AI Gateway constructs an operation-specific payload containing only approved fields.
4. The gateway assigns an opaque request identifier and records non-content audit metadata.
5. The gateway calls SALIG over the internal network using a gateway-only credential.
6. SALIG resolves the operation's approved model alias and applies resource limits.
7. LocalAI runs the pinned backend and model.
8. SALIG returns the raw model result to the gateway.
9. The gateway validates syntax, schema, enum values and safety constraints.
10. SalutApp presents the result as a draft or stores it only where the operation policy permits.

## 7. Storage boundaries

- Model files are pre-provisioned, checksummed and mounted read-only.
- Backend artifacts are supplied by the pinned image or separately approved and checksummed.
- Prompt and response bodies are not retained by default.
- Operational logs contain request identifiers, operation identifiers, timings, token counts, model aliases and outcome codes only.
- Any future vector store must be separate from MariaDB and must retain source provenance, deletion linkage and tenant boundaries.
- Generated temporary files must reside on bounded temporary storage and be removed after the request.

## 8. Availability and resource isolation

The first QNAP deployment is intentionally constrained:

- one loaded text model;
- one embedding model only when required;
- concurrency of one by default;
- bounded context and output tokens;
- explicit CPU, memory, process and temporary-storage limits;
- no direct public listener;
- startup disabled until model and image pins are approved.

SalutApp web, MariaDB, backups and storage operations have priority over inference. Resource exhaustion or model failure must fail the AI operation without degrading core health-record functions.

## 9. Evolution path

### Phase 0 — inventory

Verify QNAP model, CPU features, RAM, storage performance, available capacity, Container Station behavior and any supported accelerator.

### Phase 1 — synthetic proof of concept

Run a small CPU model with synthetic data, concurrency one and no application integration.

### Phase 2 — controlled application proof of concept

Add the SalutApp AI Gateway, operation allowlist, audit linkage, schema validation and de-identified test cases.

### Phase 3 — limited production

Permit only individually approved operations with a pinned image, approved model checksum, documented rollback and monitored resource envelope.

### Phase 4 — dedicated inference worker

Move heavy inference to a dedicated Linux GPU node while retaining policy and authorization in SalutApp.

### Phase 5 — advanced capabilities

Evaluate RAG, distributed workers or additional modalities as separate security and governance projects. Agents and unrestricted tool execution remain out of scope unless explicitly approved.