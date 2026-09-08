# Local Chuna Query Collection

## Working Contract

- Goal: CLI certificate login and collection from the e-Form Chuna query menu.
- Boundary: the certificate holder's institution, ef.hira.or.kr and extsso.hira.or.kr,
  with owner-only local results.
- Done: authenticated institution/menu, explicit treatment dates, all pages,
  total count, sequence, uniqueness and saved output verified.
- Non-goals: medical-record changes, submissions, other sites, uploads,
  credential logging, persistent browser sessions or a scheduled service.
- Verification: offline tests and an actual authenticated CLI run.

## Setup

Use macOS with Node.js 20 or newer for this CLI, an NPKI certificate/key pair,
and dependencies installed with `npm install`. Xcode Command Line Tools are
needed only to compile the password-entry helper. From the repository directory:

```bash
mkdir -p tmp
xcrun swiftc -module-cache-path /tmp/hira-swift-module-cache scripts/certificate-secret.swift -o tmp/certificate-secret
./tmp/certificate-secret set
./tmp/certificate-secret status
node scripts/verify-keychain.js
```

Run `set` yourself in Terminal. It hides entry, confirms it, and stores the password
in Keychain under service `hira-eform-macos.certificate-password`, account
`local-certificate`. Do not put the password in commands, environment variables,
chat or logs. `status` reads metadata only.

The collector requires exactly one discovered certificate pair. For multiple
pairs, set `HIRA_SIGN_CERT` and `HIRA_SIGN_KEY` to the intended paths. Invalid
explicit paths, expired certificates and mismatched keys are rejected.

## Collect

```bash
npm run collect:chuna -- --from YYYY-MM-DD --to YYYY-MM-DD
```

Both dates are inclusive **treatment dates**, not submission dates. Patient,
insurer, benefit and submission-date filters remain blank (all). The collector
uses 20 records per page, starting at page 1, and stops only when the verified
server total is collected. Missing datasets and inconsistent pagination fail
rather than being reported as an empty successful result.

No browser, `npm start`, local-agent TLS certificate or Windows PC is required.
The CLI uses the CMS signer directly and keeps its own cookies in memory. The
existing browser agent is not restarted or reconfigured.

For background execution from Terminal after Keychain access is working:

```bash
umask 077
mkdir -p tmp
nohup npm run collect:chuna -- --from YYYY-MM-DD --to YYYY-MM-DD > tmp/chuna-run.log 2>&1 &
```

Keychain may prompt for permission depending on local settings. No unrestricted
Keychain access or automatic recurrence is configured. A process launch alone is
not completion: check for `Collection complete` and the receipt.

## Output and Privacy

Each successful run creates a unique ignored directory:

```text
tmp/chuna-YYYYMMDD-YYYYMMDD-<unique>/
  results.json
  receipt.json
```

- Directory mode: `0700`; file mode: `0600`. Existing results are not overwritten.
- `results.json`: source, timestamp, date range, page counts and visible query
  fields, including patient names and birth dates. This is private medical data,
  not a public sample. Do not upload or paste it into AI chat.
- Internal patient identifier `patHpin`, institution identifier, provider license
  number, cookies, CMS, passwords and other hidden fields are not written.
- `receipt.json`: completion flag, checks, counts and result SHA-256.
- Console output contains phases/counts and the file path, not patient rows.
- JSON preserves string codes and dates; no spreadsheet conversion is performed.

The password is captured through a private subprocess pipe, not argv, environment
or inherited stdout. Signing necessarily holds plaintext in process memory.
JavaScript strings cannot be reliably wiped; the existing signer caches its
key/password until this short-lived CLI exits. Do not enable memory dumps or
sensitive capture.

## Verified HTTP Contract

1. Load `/efweb/kcase/pkiLogin.jsp` with a fresh cookie jar.
2. Sign the certificate DN using the existing CP949 CMS format.
3. POST `gid`, `signeddata`, `returl` to the extsso certificate-login endpoint.
4. Submit returned `pmisso` forms (`pmi-sso-return`, then `pmi-sso-return2`) to
   `/efweb/pkiLogin.ndo`, following normal HTTPS redirects.
5. Parse, never execute, the completion page's literal `document.location.href`.
   Only the expected HIRA destination is accepted.
6. POST `/efweb/isLogin.do` with `APP_YN=Y`. Require one institution and menu
   `EF05010002` in the response; derive `ykiho` from this authenticated session.
7. POST `/efweb/ie/ier/selectChnaSmitInqL.do` with `dsCond`: `ykiho`, `diagDdStd`,
   `diagDdEnd`, `fetchRow=20`, `pageNum`, and blank other filters.
8. Parse `dsList`, validate all pages, then persist the minimal result locally.

Nexacro 14 SSV uses RS (`0x1e`) between records, US (`0x1f`) between fields, ETX
(`0x03`) for null. HIRA labels these responses `text/html` despite the SSV body.
Success may omit `ErrorCode`; the original client defaults it to zero. The
collector additionally requires expected datasets.

Live public sources checked on 2026-09-08:

- `/efweb/hira_ef/efweb/ier/yadmChnaSmitListInqL.xfdl.js`
- `/efweb/hira_ef/comm/comPaging.xfdl.js`
- `/efweb/hira_ef/nexacro14lib/component/CompBase/Data.js`

These define bindings, page numbering and SSV. No provider source or authenticated
response fixture is included in this repository.

## Verification (2026-09-08)

- Keychain password decrypted the selected key and matched its certificate.
- Actual CLI certificate login, treatment-date query and local output verification
  succeeded. Actual dates, counts and patient records are intentionally omitted
  from public documentation; they belong only in local result files.
- macOS curl timed out; Node.js fetch succeeded. The curl-specific cause has not
  been established.
- `npm run test:collector` runs synthetic parser/date/destination/pagination and
  publication checks with no real credentials or network. Multi-page behavior is covered
  synthetically; the live result required one page.
- Concurrent changes preserving total count are not a transactional snapshot
  guarantee. Count/sequence/duplicate checks detect common drift only.
- Other certificate issuers, multi-user accounts and future site changes remain
  unverified. Unexpected authentication flows fail closed.
