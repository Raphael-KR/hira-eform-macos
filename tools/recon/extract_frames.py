#!/usr/bin/env python3
"""Extract WebSocket frames from CDP capture JSONL and decode KCase envelopes."""

import json
import base64
import sys
from pathlib import Path

path = Path(sys.argv[1] if len(sys.argv) > 1 else "hira-capture.jsonl")

sockets = {}   # requestId -> url
events = []    # list of (timestamp, kind, requestId, url, payload)

with path.open() as f:
    for line in f:
        try:
            obj = json.loads(line)
        except Exception:
            continue
        m = obj.get("method")
        p = obj.get("params") or {}
        if m == "Network.webSocketCreated":
            sockets[p["requestId"]] = p["url"]
            events.append((0, "CREATE", p["requestId"], p["url"], ""))
        elif m == "Network.webSocketFrameSent":
            rid = p["requestId"]
            ts = p.get("timestamp", 0)
            data = p.get("response", {}).get("payloadData", "")
            events.append((ts, "SENT", rid, sockets.get(rid, "?"), data))
        elif m == "Network.webSocketFrameReceived":
            rid = p["requestId"]
            ts = p.get("timestamp", 0)
            data = p.get("response", {}).get("payloadData", "")
            events.append((ts, "RECV", rid, sockets.get(rid, "?"), data))
        elif m == "Network.webSocketClosed":
            events.append((p.get("timestamp", 0), "CLOSE", p["requestId"], sockets.get(p["requestId"], "?"), ""))

# sort by timestamp, but keep CREATE events first (ts=0)
events.sort(key=lambda e: (e[0] == 0 and e[1] != "CREATE", e[0]))

# Filter to KCase (localhost:8443) only for summary
print(f"Total WS events: {len(events)}")
urls = set(sockets.values())
for u in urls:
    n = sum(1 for e in events if e[3] == u)
    print(f"  {u}  ({n} events)")
print()

def decode_envelope(payload):
    """Decode KCase '1data=<json>' style frames and JSON responses."""
    if payload.startswith("0") and "open" in payload[:20]:
        return "HANDSHAKE: " + payload
    if payload.startswith("1data="):
        try:
            env = json.loads(payload[len("1data="):])
            sess = env.get("SessionId", "")
            method = env.get("Method", "")
            data_b64 = env.get("Data", "")
            try:
                decoded = base64.b64decode(data_b64)
                # sessionKeyId + JSON.stringify(sendObj) [non-secure]
                # Try parsing as JSON first
                text = decoded.decode("utf-8", errors="replace")
                # look for JSON start
                i = text.find("{")
                if i >= 0:
                    prefix = text[:i]
                    rest = text[i:]
                    try:
                        j = json.loads(rest)
                        return f"ENV method={method} sid={sess} keyIdPrefix={prefix!r} payload={json.dumps(j, ensure_ascii=False)}"
                    except Exception:
                        return f"ENV method={method} sid={sess} raw(utf8)={text!r}"
                return f"ENV method={method} sid={sess} raw(utf8)={text!r}"
            except Exception as e:
                return f"ENV method={method} sid={sess} Data(b64)={data_b64[:100]}... decode_err={e}"
        except Exception as e:
            return f"1data= parse err: {e}  raw={payload[:200]}"
    # server response: may be raw JSON
    try:
        j = json.loads(payload)
        return f"RESP {json.dumps(j, ensure_ascii=False)[:400]}"
    except Exception:
        return f"RAW {payload[:200]}"

print("=" * 80)
for i, (ts, kind, rid, url, data) in enumerate(events):
    if "127.0.0.1:8443" not in url and kind != "CREATE":
        continue
    if kind == "CREATE":
        print(f"[{i:03d}] {ts:>14} {kind:5} url={url}")
        continue
    if kind == "CLOSE":
        print(f"[{i:03d}] {ts:>14.3f} {kind:5}")
        continue
    decoded = decode_envelope(data)
    print(f"[{i:03d}] {ts:>14.3f} {kind:5} {decoded}")
