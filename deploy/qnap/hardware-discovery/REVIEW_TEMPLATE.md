# SALIG QNAP Hardware Suitability Review

> Complete this worksheet only from the private discovery evidence. Use `unknown` where the report does not prove a fact. Do not infer or estimate missing host characteristics.

## Evidence identity

- Evidence filename:
- Evidence SHA-256:
- `COLLECTED_AT_UTC`:
- `DISCOVERY_RESULT`:
- Reviewer:
- Review date:
- Redaction applied to review copy: yes / no

## 1. Platform identity

- QNAP model:
- Firmware/QTS/QuTS version and build:
- Kernel:
- Architecture:
- Docker/Container Station engine version:
- Docker Compose version:
- Material collection gaps:

## 2. CPU compatibility

- CPU model:
- Physical cores:
- Logical CPUs:
- Required instruction flags observed:
- AVX present: yes / no / not applicable / unknown
- AVX2 present: yes / no / not applicable / unknown
- Architecture-compatible CPU backend available for later testing: not assessed / candidate / blocked
- CPU compatibility finding:

## 3. Memory envelope

- Total RAM:
- Available RAM at collection:
- Swap total and use:
- Existing container memory use:
- Evidence of memory pressure:
- Conservative RAM available for a POC after SalutApp safety margin:
- Memory finding:

## 4. Storage envelope

- Docker root directory:
- Filesystem and media type for Docker root:
- Free capacity:
- SSD/NVMe visibility:
- RAID state observations:
- I/O sample observations:
- Space reserved for images, backend, one model and temporary files:
- Storage finding:

## 5. Existing workload and contention risk

- Running container count:
- SalutApp-related containers observed:
- Highest CPU consumer in snapshot:
- Highest memory consumer in snapshot:
- Host load during collection:
- Known backup or maintenance windows: not proven by collector / separately evidenced
- Contention risk:

## 6. Docker and isolation feasibility

- Required Docker networks observed:
- Candidate shared SalutApp internal network:
- Network-name or subnet conflict:
- Cgroup version and driver:
- Resource-limit support concern:
- Read-only model/configuration mount feasibility: not yet runtime-tested
- No-host-port design feasibility: not yet runtime-tested
- Isolation finding:

## 7. Accelerator and thermal visibility

- GPU/accelerator detected:
- Relevant device nodes:
- Runtime tooling detected:
- Thermal sensors visible:
- Temperature observations:
- Accelerator use in first POC: prohibited / not required / candidate for later review
- Thermal finding:

## 8. Evidence quality

- Failed commands:
- Unavailable optional commands:
- Missing material facts:
- Additional read-only collection required:
- Evidence sufficient for route decision: yes / no

## 9. Route decision

Select exactly one:

- [ ] **Route A — QNAP POC candidate.** Prepare a constrained CPU-only synthetic proof-of-concept profile. This is not production approval.
- [ ] **Route B — dedicated private inference node required.** Keep QNAP as the SalutApp control plane and perform inference on a separate private Linux host.
- [ ] **Decision deferred.** The evidence is incomplete; perform the listed additional read-only discovery first.

### Decision rationale


### Binding constraints for the next phase

- Maximum candidate model class:
- Maximum initial context:
- Initial concurrency:
- CPU/memory limits to test:
- Storage budget to reserve:
- Required maintenance or test window:
- Other constraints:

## 10. Approval boundary

This review approves only the route decision for the next synthetic POC design step. It does not approve a LocalAI image, backend, model, license, model download, runtime network change, protected-data processing or production deployment.
