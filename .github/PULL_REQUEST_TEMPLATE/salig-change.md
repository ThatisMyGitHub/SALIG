## SALIG change summary

Describe the purpose and scope of this change.

## Target branch

- [ ] This pull request targets `salig/integration`.
- [ ] This change does not add SALIG-specific commits to `master`.

## Upstream and artifact pins

- LocalAI upstream commit:
- SALIG source base:
- Container image digest, when applicable:
- Backend digest or checksum, when applicable:
- Model alias and SHA-256, when applicable:
- Configuration checksum, when applicable:

## Security impact

- [ ] No direct SalutApp database access was added.
- [ ] No public or host LocalAI port was added.
- [ ] No cloud inference or protected-data egress was added.
- [ ] Agents, MCP and runtime downloads remain disabled unless separately approved.
- [ ] No secret or protected content is included in code, logs, tests or evidence.
- [ ] Input minimisation and output validation remain owned by the SalutApp AI Gateway.

Explain any changed trust boundary, data class, caller, operation, retention rule or model capability:

## Validation

- [ ] Configuration validation completed.
- [ ] Synthetic functional tests completed.
- [ ] Authorization-denial tests completed or are not applicable.
- [ ] Resource-limit and timeout tests completed or are not applicable.
- [ ] Logs were checked for protected content.
- [ ] Upgrade and rollback impact was assessed.

Test evidence:

## Rollback

State the exact source, image, configuration and model revisions required to roll back this change.

## Approval

- [ ] The model or operation allowlist was updated when required.
- [ ] Documentation reflects the deployed behavior.
- [ ] All review conversations are resolved.
