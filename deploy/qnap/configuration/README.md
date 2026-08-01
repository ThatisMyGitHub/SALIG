# Approved LocalAI Configuration

This directory is mounted read-only at `/configuration` inside the SALIG container.

No active model configuration is committed in the initial baseline because no image, backend or model has yet been approved.

Before adding a configuration:

1. Select the exact digest-pinned LocalAI image.
2. Confirm the configuration schema supported by that image.
3. Select an approved backend included in, or immutably provisioned for, the image.
4. Place the approved model file in the QNAP `/models` bind mount.
5. Record the model in `salig/model-allowlist.yaml` with its SHA-256 checksum and permitted operations.
6. Ensure the configuration references only local files under `/models`.
7. Reject remote URLs, gallery identifiers and runtime installation instructions.
8. Set bounded context, output and resource parameters.
9. Test with synthetic data and retain the configuration checksum in the release evidence.

Configuration filenames should use stable application-facing aliases, for example:

```text
salig-text-small.yaml
salig-embedding-small.yaml
```

SalutApp must refer to the approved alias, never to an arbitrary model path or user-supplied model name.
