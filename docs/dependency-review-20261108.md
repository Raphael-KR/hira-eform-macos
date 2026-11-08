# Dependency review: 2026-11-08

## Scope and completion criteria

- Goal: review and publish the existing dependency edits and pending documentation commit.
- Scope: package manifests, their Node requirement, and the pending runtime-audit documentation.
- Completion: focused offline checks pass, commits are published without rewriting history, and Git state is reported.
- Exclusions: live HIRA access, certificate login, generated test credentials/data, app restart, deployment, rollback, and unrelated changes.
- Verification: manifest/lock/install consistency, dependency imports, tracked JavaScript syntax, existing authentication-parser test, and publication check.

## Findings

The original author and command responsible for the uncommitted dependency edits are unconfirmed. The edits update acorn 8.18.0 to 8.19.0, cheerio 1.0.0 to 1.2.0, iconv-lite 0.7.2 to 0.7.3, and ws 8.21.3 to 8.22.0, with corresponding transitive lockfile updates. The installed direct dependencies match the lockfile. These updates are retained as dependency maintenance, not claimed to be necessary security fixes.

Cheerio and its updated undici dependency declare Node >=20.18.1 in the lockfile. The root package, root lockfile metadata, and README now use that minimum instead of >=20. Existing CI selects major Node versions 20, 22, and 24; those CI jobs were not run locally.

The pending commit 02398eaeaf6f85296c32e3b591cf3820d50ad8ea changes only ddmd/README.md and docs/HISTORY.md. It documents prior runtime inspection and an installed-app Node path repair; publishing it does not perform that repair again. Remote fetch showed zero remote-only commits and one local-only commit before this review. Its historical runtime claims were not re-executed.

## Local checks

Environment: Node v26.13.0. No dependency installation was performed.

- npm ls --depth=0 --offline: passed, six direct dependencies.
- Manifest dependencies and engines equal root lockfile metadata: passed.
- Direct installed versions equal lockfile versions and all six imports succeed: passed.
- node --check for all 40 tracked JavaScript files: passed.
- Existing test selected by `node --test --test-name-pattern='authentication rejects' scripts/test-collector.js`: one passed. Uses existing inline fixtures; no new fixture or database was created and no network request was made.
- npm run check:release before editing: 107 files, zero findings.

The full npm test suite was not run because it includes generated signing fixtures and local server startup. No claim is made about live login, cryptographic integration, WebSocket runtime behavior, or minimum-Node execution. Source publication is distinct from deployment.
