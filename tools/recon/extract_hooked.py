#!/usr/bin/env python3
"""Extract plaintext KCase API calls and WS frames from hooked CDP capture."""

import json
import base64
import sys
from pathlib import Path

path = Path(sys.argv[1] if len(sys.argv) > 1 else "hira-hooked.jsonl")

log_tag = "__KCASE_HOOK__ "
events = []  # (ts, kind, rest)

with path.open() as f:
    for line in f:
        try:
            obj = json.loads(line)
        except Exception:
            continue
        m = obj.get("method")
        p = obj.get("params") or {}
        ts = p.get("timestamp") or 0

        if m == "Runtime.consoleAPICalled":
            # We log one string arg; extract it
            args = p.get("args") or []
            if not args:
                continue
            s = args[0].get("value", "")
            if not s or not s.startswith(log_tag):
                continue
            rest = s[len(log_tag):]
            events.append((ts, "HOOK", rest))
        elif m == "Network.webSocketCreated":
            if "127.0.0.1:8443" in p.get("url", ""):
                events.append((ts, "WS_CREATE", p["url"]))
        elif m == "Network.webSocketFrameSent":
            if "8443" in str(p):  # heuristic
                data = p.get("response", {}).get("payloadData", "")
                events.append((ts, "WS_SENT", data))
        elif m == "Network.webSocketFrameReceived":
            if "8443" in str(p):
                data = p.get("response", {}).get("payloadData", "")
                events.append((ts, "WS_RECV", data))

# Sort hook events by their natural order (they came in-order from Runtime.consoleAPICalled
# so CDP timestamp of consoleAPICalled is correct). But CDP events and console events
# share the same ts scale, so the full sort is ok.
events.sort(key=lambda e: e[0])

# Print everything, focused on HOOK events (they carry the gold)
def dec_envelope(env_str):
    """env_str is the JSON part after '1data='."""
    try:
        env = json.loads(env_str)
    except Exception:
        return None
    try:
        sess_raw = base64.b64decode(env.get("SessionId", "")).decode("utf-8", errors="replace")
    except Exception:
        sess_raw = env.get("SessionId", "")
    data = env.get("Data", "")
    try:
        d = base64.b64decode(data)
        # Try utf-8 JSON after optional binary prefix
        s = d.decode("utf-8", errors="replace")
        i = s.find("{")
        if i >= 0:
            prefix_b = d[:i]
            try:
                inner = json.loads(s[i:])
                return {
                    "session": sess_raw,
                    "method": env.get("Method"),
                    "keyid_hex": prefix_b.hex(),
                    "keyid_len": len(prefix_b),
                    "inner": inner,
                }
            except Exception:
                return {
                    "session": sess_raw,
                    "method": env.get("Method"),
                    "keyid_hex": prefix_b.hex(),
                    "raw_text": s,
                }
        return {"session": sess_raw, "method": env.get("Method"), "data_hex": d.hex()[:200]}
    except Exception as e:
        return {"session": sess_raw, "method": env.get("Method"), "err": str(e)}

print(f"=== Summary: {len(events)} total events ===\n")

hook_lines = [(ts, rest) for ts, kind, rest in events if kind == "HOOK"]
ws_lines = [(ts, kind, rest) for ts, kind, rest in events if kind in ("WS_SENT", "WS_RECV", "WS_CREATE")]
print(f"HOOK events: {len(hook_lines)}   WS events: {len(ws_lines)}\n")

# First pass: print all HOOK events (they're the plaintext gold)
print("=" * 90)
print("HOOK EVENTS (plaintext API calls & callbacks)")
print("=" * 90)
for ts, rest in hook_lines:
    # Parse "LABEL <space> {json}"
    sp = rest.find(" ")
    if sp < 0:
        print(f"[{ts:10.3f}] {rest}")
        continue
    label = rest[:sp]
    payload = rest[sp+1:]
    # Skip HOOK_TIMEOUT noise after first few
    if label == "HOOK_TIMEOUT":
        continue
    print(f"\n[{ts:10.3f}] {label}")
    # For WS_SEND with 1data= format, decode the envelope
    if label == "WS_SEND":
        try:
            j = json.loads(payload)
            d = j.get("data", "")
            if d.startswith("1data="):
                env = dec_envelope(d[len("1data="):])
                print("    ENVELOPE:", json.dumps(env, ensure_ascii=False, indent=6, default=str))
            else:
                print("    data:", d)
        except Exception as e:
            print("    parse_err:", e, payload[:200])
    elif label == "WS_RECV":
        try:
            j = json.loads(payload)
            d = j.get("data", "")
            try:
                inner = json.loads(d) if d else {}
                print("    RESP:", json.dumps(inner, ensure_ascii=False, indent=6)[:800])
            except Exception:
                print("    raw:", d[:300])
        except Exception as e:
            print("    parse_err:", e)
    else:
        # Generic pretty print
        try:
            j = json.loads(payload)
            txt = json.dumps(j, ensure_ascii=False, indent=6)
            if len(txt) > 2000:
                txt = txt[:2000] + "\n      ...[truncated]"
            print("   ", txt)
        except Exception:
            print("   ", payload[:500])
