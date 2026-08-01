# `salig/integration` Branch Protection

The GitHub connector can create and update repository content but does not expose repository ruleset or branch-protection administration. Apply the following settings manually in GitHub immediately after this baseline is created.

## Recommended ruleset

Create a branch ruleset named:

```text
SALIG integration protection
```

Target branch pattern:

```text
salig/integration
```

Set the ruleset to **Active** and enable:

- Restrict deletions.
- Block force pushes.
- Require a pull request before merging.
- Require all conversations to be resolved before merging.
- Require linear history.
- Require signed commits when the team's signing workflow is ready and verified.
- Require status checks once SALIG validation workflows are added.
- Require deployments to succeed only when a protected deployment environment is later introduced.

For the initial single-owner repository, configure the pull-request rule so the owner can merge a reviewed and resolved pull request without creating an impossible self-approval requirement. When a second trusted reviewer is added, require at least one approval and enable dismissal of stale approvals.

## Bypass policy

- Do not grant routine bypass to applications or automation.
- Repository administrator bypass should be limited to emergencies.
- Every bypass must be documented in an issue or pull request with the reason, affected commit, validation performed and follow-up review.

## Master branch

Create a separate ruleset for `master` that:

- restricts deletions;
- blocks force pushes;
- prevents SALIG feature pull requests from targeting `master`;
- permits only reviewed upstream synchronization;
- preserves its role as the clean upstream-derived branch.

Do not merge `salig/integration` into `master`.

## Verification

After applying the ruleset:

1. Confirm that a direct push to `salig/integration` is rejected.
2. Confirm that a feature branch can open a pull request targeting `salig/integration`.
3. Confirm that unresolved conversations block merging.
4. Confirm that force-push and deletion are blocked.
5. Confirm that `master` remains unchanged by the initial SALIG commits.

Record a screenshot or exported ruleset summary in protected operational evidence, not in a public issue if it contains account or security details.
