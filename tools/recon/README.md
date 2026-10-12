# Local protocol investigation tools

Historical diagnostic scripts, not part of the login runtime. No captured data
or credentials are included. Compatibility with current Windows/Chrome versions
has not been retested.

- `launch-chrome.ps1`: Windows Chrome with a dedicated profile and CDP port 9222.
- `capture-cdp.ps1`: collect CDP network events into JSONL.
- `capture-cdp-hooked.ps1`: additionally instrument KCase calls and callbacks.
- `extract_frames.py`: decode a capture supplied as the first argument.
- `extract_hooked.py`: summarize a hooked capture supplied as the first argument.

On an authorized Windows test machine, launch Chrome, start one capture script
in another PowerShell window, perform the test manually, then stop capture with
Ctrl+C. Capture defaults and the isolated browser profile are under `C:\Temp`.
Analyze an explicit capture path with Python 3; output goes to stdout.

WARNING: capture and analysis output is NOT redacted. It can contain passwords,
cookies, session identifiers, certificate details and authentication signatures.
The capture scripts can fall back to the first page if no HIRA page matches;
use only a dedicated test browser with no unrelated tabs. Do not publish output
or paste it into shared chats. Remove captures, reports and the test profile
after use. Never expose the debugging port to a network.

Only these five scripts and this README are allowed in Git here. Existing
protocol conclusions are in [SIGN_FLOW](../../docs/SIGN_FLOW.md) and
[HISTORY](../../docs/HISTORY.md). The parsers use historical heuristics and are
not a replacement for the runtime protocol implementation.
