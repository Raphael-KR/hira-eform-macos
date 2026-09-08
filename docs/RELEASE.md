# Public Release Preparation

## Scope

Publish implementation, synthetic tests and generic documentation only. Never
include collection results (including count receipts), certificate files, password
stores, CMS signatures, cookies, browser profiles, network captures or real-account
fixtures. Preserve these locally; exclusion does not mean deletion.

## Checks

```bash
npm ci
npm test
npm run check:release
npm audit --omit=dev
git diff --check
git status --short
```

Tests use synthetic certificates and isolated ephemeral loopback ports. They do
not read Keychain, call HIRA or replace the user's trusted local TLS certificate.
The GitHub Actions workflow runs the same tests and public candidate check.

`check:release` examines tracked and non-ignored untracked candidates against a
source-file allowlist, then checks for embedded credentials, large base64 literals,
owner paths and resident-number-shaped values. It rejects unexpected files before
reading them. In particular, `.gitignore` does not protect an already tracked file;
the candidate check is independent of that protection.

This is a guardrail, not proof that every possible secret or patient detail is
absent. Review documentation and staged changes, and use a dedicated secret scanner
on both Git history and a copy of the publication candidates before publishing.
Scanner reports must also remain ignored and local.

## Release Content

- Keychain-backed CLI authentication and read-only Chuna query collection.
- Strict treatment dates, pagination validation and owner-only JSON output.
- Payload-free agent diagnostics and Keychain-backed standalone signing checks.
- Removed the obsolete experimental KDF diagnostic accepting passwords in argv.
- Node.js 20 minimum; supported-major ws security patch update.
- Source-only publication guard and CI test coverage.

Before committing, stage specific reviewed source paths, not ignored files with
`git add -f`. Inspect the index again. Commit, push, tag and GitHub release creation
are separate actions requiring the requested authorization. No automatic upload is
part of the collector or release checker.

The browser agent's current runtime is unchanged until explicitly restarted.
These checks do not establish legal clearance or broad compatibility beyond the
documented e-Form flow.
