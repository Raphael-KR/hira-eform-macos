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
npm run test:app
npm run check:release
npm audit --omit=dev
git diff --check
git status --short
```

Tests use synthetic certificates and isolated ephemeral loopback ports. They do
not read Keychain, call HIRA or replace the user's trusted local TLS certificate.
The GitHub Actions workflow runs the base tests and public candidate check.
The app lifecycle check is also run locally for menu-bar releases.

`check:release` examines tracked and non-ignored untracked candidates against a
source-file allowlist, then checks for embedded credentials, large base64 literals,
owner paths and resident-number-shaped values. It rejects unexpected files before
reading them. In particular, `.gitignore` does not protect an already tracked file;
the candidate check is independent of that protection.

This is a guardrail, not proof that every possible secret or patient detail is
absent. Review documentation and staged changes, and use a dedicated secret scanner
on both Git history and a copy of the publication candidates before publishing.
Scanner reports must also remain ignored and local.

## App Release

The v1.0.0 app is a repository-connected local build, not a standalone notarized
distribution. Its version comes from package.json; package-lock.json must agree.
Build with `npm run build:app`, inspect the printed bundle's Info.plist and verify
its ad-hoc signature with `codesign --verify --deep --strict "<app path>"`.
The bundle must contain no certificate, credential or collected data. Do not
publish local runtime paths or ignored dist bundles as a public binary release.

Installing/replacing an app and running GUI smoke checks are separate from source
checks. Keep the existing app stopped before replacement; do not restart a user's
server as part of documentation or release-candidate inspection.
Use [MENUBAR_APP](MENUBAR_APP.md) for the build/use contract.

## Documentation and Git

Development and experiment results are in [e-Form history](HISTORY.md) and
[DDMD history](../ddmd/docs/HISTORY.md). Keep current commands in the runbooks,
not duplicated across historical reports. Before consolidation, snapshot the
documents locally; preserve tables and failed tests, then verify relative links
and that no private evidence was copied into the public replacement.

Before committing, stage specific reviewed source paths, not ignored files with
`git add -f`. Inspect the index again. Commit, push, tag and GitHub release creation
are separate actions requiring the requested authorization. No automatic upload is
part of the collector or release checker.

The browser agent's current runtime is unchanged until explicitly restarted.
These checks do not establish legal clearance or broad compatibility beyond the
documented e-Form flow.
