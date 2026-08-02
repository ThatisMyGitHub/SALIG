# SALIG QNAP Hardware Discovery Package

## Purpose

This package prepares the first platform-dependent SALIG milestone while no QNAP access is available. It collects the minimum host, CPU, memory, storage, Docker/Container Station, network, accelerator and thermal facts needed to decide whether the current QNAP can support the first private CPU inference proof of concept.

The package does **not** approve hardware, select a model, download an image, start a container, inspect container environment variables, access MariaDB, or change any host or Docker configuration.

## Package contents

- `collect-qnap-hardware.sh` — read-only collector that writes one private timestamped report.
- `verify-qnap-hardware-evidence.sh` — validates the report structure and prints its SHA-256 without displaying the report.
- `REVIEW_TEMPLATE.md` — assessment worksheet to complete after the evidence is available.
- `MANIFEST.txt` — package scope, order and expected outputs.
- `SHA256SUMS` — integrity checksums for the package files.

Repository regression tests enforce shell syntax, output-location safeguards and the absence of prohibited mutation or secret-dumping commands.

## Safety properties

The collector:

- requires an explicit absolute output directory;
- refuses to write inside the Git repository;
- creates evidence with `umask 077` and attempts mode `0600`;
- does not use `sudo`;
- does not start, stop, restart, create, remove, pull or update containers or Docker objects;
- does not run `docker inspect` against containers;
- does not dump process, container or host environment variables;
- does not read SalutApp files, MariaDB, model files or application data;
- continues when optional QNAP/Linux commands are unavailable and records the gaps.

The report is private operational evidence. It can contain a hostname, filesystem paths, Docker image names, Docker network names and IPAM subnets. Do not commit it to Git or send it through public channels.

## Preconditions when platform access becomes available

1. Terminal or SSH access to the QNAP host.
2. A local clone of this repository checked out on `salig/integration`.
3. Permission to run read-only Docker commands. The collector remains useful without that permission, but the resulting evidence will be incomplete.
4. A private output directory outside the repository.
5. No maintenance window is required because the collector does not alter running services.

## Canonical host execution command

Set the two paths to the real repository and private evidence locations, then run the entire block from the QNAP host:

```sh
SALIG_REPO=/share/data/dockerapps/SALIG
SALIG_EVIDENCE_DIR=/share/data/dockerapps/salig-private/evidence

cd "$SALIG_REPO" &&
git fetch origin &&
git checkout salig/integration &&
git pull --ff-only origin salig/integration &&
sh deploy/qnap/hardware-discovery/collect-qnap-hardware.sh \
  --output-dir "$SALIG_EVIDENCE_DIR"
```

This is the only collection command. Do not add `sudo`, redirect the report into the repository, or run the script by sourcing it into the current shell.

## Verify the generated evidence

The collector prints the exact evidence path. Verify that file with:

```sh
SALIG_REPO=/share/data/dockerapps/SALIG
EVIDENCE_FILE=/share/data/dockerapps/salig-private/evidence/salig_qnap_hardware_discovery_YYYYMMDDTHHMMSSZ.txt

cd "$SALIG_REPO" &&
sh deploy/qnap/hardware-discovery/verify-qnap-hardware-evidence.sh \
  "$EVIDENCE_FILE"
```

The verifier prints only structural status, collection counters and the SHA-256. It does not print the evidence body.

## Evidence handling

1. Keep the original report unchanged and private.
2. Record the verifier SHA-256 in the private assessment record.
3. Review the report locally before transferring it.
4. Redact only a separate copy when a hostname, path, image name, network name or address is not needed for review.
5. Never commit the original or redacted report to this public source tree.
6. Provide the private evidence to the SALIG review process together with the completed `REVIEW_TEMPLATE.md`.

## Expected report sections

The report has format version `1` and contains:

1. Host identity and QNAP release.
2. CPU and instruction set.
3. Memory, load and cgroups.
4. Storage and filesystems.
5. Docker and Container Station.
6. Accelerator and PCI devices.
7. Thermal visibility.
8. Collection summary.

`DISCOVERY_RESULT=COLLECTED_WITH_GAPS` does not automatically disqualify the host. Every failed or unavailable command must be reviewed to determine whether the missing fact is material.

## Decision after collection

The evidence supports one of two decisions only:

- **Route A — QNAP POC candidate:** measured resources and compatibility justify a constrained CPU-only synthetic proof of concept.
- **Route B — dedicated inference node required:** the QNAP remains the SalutApp control plane, while inference is placed on a separate private Linux host.

No model, image, backend or production deployment is approved by this discovery package or by completing the worksheet.

## Rollback

This milestone is repository-only. Rollback is closing or reverting its pull request. Running the collector later creates only the named evidence file and, if necessary, its output directory. Removing those private evidence artifacts is the only host cleanup; no service or configuration rollback is required.
