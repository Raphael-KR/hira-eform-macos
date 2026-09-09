# e-Form Menu Bar App

Version 1.0.0: approved by the owner after local testing. The local app can be
installed as `/Applications/HIRA e-Form.app`. Package and bundle versions share
the `package.json` version. This remains a repository-connected local build,
not a notarized standalone distribution.

## Working Contract

- Goal: launch a macOS app and start or stop the existing e-Form agent
  from the menu bar, with visible lifecycle status.
- Boundary: native Swift/AppKit shell, existing local Node server and its TLS files.
- Done: local signed app builds; isolated lifecycle tests pass; the owner
  confirmed menu behavior on this Mac.
- Non-goals: native rewrite of PKI, CLI collection UI, credential copies, automatic
  login items, privileged helpers, automatic certificate trust, public binary release.
- Verification: Swift compiler, ad-hoc code signature, synthetic Node lifecycle
  tests and local menu-bar smoke checks. Other macOS versions are not implied tested.

## Architecture

AppKit `NSStatusItem` + `NSMenu` manages a Foundation `Process`. The process runs
`scripts/menubar-agent.js` using the locally installed Node executable, with a
minimal environment and the project directory as its working directory.
Both HTTPS listeners must be ready before reporting running. Heartbeats come
only through the child process pipe, not an unrelated service on the same port.
Closing the app's pipe stops the child even if the app exits unexpectedly.

The app never adopts/kills processes launched by Terminal or other apps. If either
8443 or 39091 is occupied, it reports a conflict and leaves that process alone.
Stop the earlier Terminal server yourself before using the app's start command.
To restart, stop the server and then start it after shutdown completes.

## Build and Use

```bash
npm run build:app
```

Open the printed `dist/build-*/HIRA e-Form.app` path. Each build is separate and
does not overwrite an existing app. The menu contains one server control, open e-Form,
and quit. Only start is shown without an owned server; only stop is shown with one.
The control is disabled during startup/shutdown or when an external port conflict
prevents starting. There is no separate restart item.
It starts stopped; launching the app does not initiate certificate login
or read Keychain. Select start before using the site's certificate login.

The menu bar shows only `eF`, in 12-point bold system font, matching IPinsideMock.
Running uses `NSColor.systemGreen`; stopped, starting and stopping use
`NSColor.systemGray`; errors and port conflicts use `NSColor.systemRed`.
These are Apple's adaptable standard colors, not fixed RGB values. The menu text,
tooltip and accessibility label also describe state without relying on color.
IPinsideMock uses orange for incomplete setup; this app uses red for problems as
requested. See [Apple standard colors](https://developer.apple.com/documentation/appkit/standard-colors).

The app bundle icon is an original AI-generated blue layered-document illustration
with the lowercase label `e-form`,
not an official HIRA logo. Its source is `macos/assets/AppIcon.png`. The build uses
macOS `sips` and `iconutil` to produce the 16-1024 pixel icon representations and
sets `CFBundleIconFile`. This does not change the text-only menu bar item.

This is a **local, repository-connected launcher**, not a standalone distributable.
It needs the project folder, installed Node/dependencies and existing TLS files.
The ignored bundle embeds only local runtime paths, not certificates, passwords or
collection results. If the repository or Node moves, rebuild the app. The `.app`
may be copied elsewhere on this same Mac without moving the repository.

Build target: macOS 12+, host architecture only. Bundle identifier:
`kr.raphael.hira-eform-macos`. Ad-hoc signing, no App Sandbox, no Developer ID or
notarization. External-process control and existing NPKI access require this local
unsandboxed posture. No Accessibility permission is required for normal app use.
Do not present this local build as a notarized public release.

## Verification

`npm run test:app` uses synthetic TLS and ephemeral ports to check both-listener
readiness, stdin-EOF shutdown, a fresh start after shutdown, port conflict without
affecting the existing listener, and missing TLS failure. It never reads NPKI.
`npm test` exercises the existing signing, protocol and collection regressions.

As of 2026-09-09, the local Swift build, ad-hoc signature verification and both
CLI test commands passed on Apple Silicon. The owner separately launched the app
and confirmed its behavior. The agent did not perform GUI interaction because
the owner selected CLI-only testing. Accessibility and other macOS versions remain
unverified. See [development history](HISTORY.md) for the release context.

Apple API references: [NSStatusItem](https://developer.apple.com/documentation/appkit/nsstatusitem),
[Process terminationHandler](https://developer.apple.com/documentation/foundation/process/terminationhandler).
