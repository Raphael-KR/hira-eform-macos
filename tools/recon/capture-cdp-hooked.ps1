#requires -Version 5.1
<#
.SYNOPSIS
  Attach to Chrome on CDP port 9222, inject a monkey-patch that logs plaintext
  KCase Agent API calls, and capture both the WebSocket frames AND the
  console.log output (which contains the plaintext).

.DESCRIPTION
  The injected JS wraps kcaseagt._daemonServiceRequest_Init (the WSS request fn)
  to log { sendObj } before encryption and { jsonObj } after decryption.
  Runs on every page load via Page.addScriptToEvaluateOnNewDocument.

  Workflow:
    1. launch-chrome.ps1 (if not already up)
    2. This script (attaches and installs the hook)
    3. In the Chrome window: hit Ctrl+F5 to reload ef.hira.or.kr, then login
    4. Ctrl+C this script when done

.PARAMETER OutFile
  JSONL log path. Default: C:\Temp\hira-hooked.jsonl
#>
param(
    [string]$OutFile = "C:\Temp\hira-hooked.jsonl",
    [string]$TargetPattern = "hira\.or\.kr"
)

$ErrorActionPreference = "Stop"

$dir = Split-Path -Parent $OutFile
if ($dir -and -not (Test-Path $dir)) { New-Item -ItemType Directory -Path $dir -Force | Out-Null }

Write-Host "Locating CDP targets..."
$targets = Invoke-RestMethod -Uri "http://127.0.0.1:9222/json/list" -TimeoutSec 5
$target = $targets | Where-Object { $_.type -eq "page" -and $_.url -match $TargetPattern } | Select-Object -First 1
if (-not $target) {
    $target = $targets | Where-Object { $_.type -eq "page" } | Select-Object -First 1
}
if (-not $target) { Write-Error "No CDP page target."; exit 1 }

Write-Host "Attaching: $($target.title) [$($target.url)]"
$ws = [System.Net.WebSockets.ClientWebSocket]::new()
$ws.Options.KeepAliveInterval = [TimeSpan]::FromSeconds(30)
$ws.ConnectAsync([Uri]::new($target.webSocketDebuggerUrl), [Threading.CancellationToken]::None).GetAwaiter().GetResult() | Out-Null

$msgId = 0
function Send-Cmd {
    param([string]$Method, $Params)
    $script:msgId++
    $obj = [ordered]@{ id = $script:msgId; method = $Method }
    if ($Params) { $obj.params = $Params }
    $json = $obj | ConvertTo-Json -Compress -Depth 25
    $bytes = [System.Text.Encoding]::UTF8.GetBytes($json)
    $seg = [ArraySegment[byte]]::new($bytes)
    $ws.SendAsync($seg, [System.Net.WebSockets.WebSocketMessageType]::Text, $true, [Threading.CancellationToken]::None).GetAwaiter().GetResult() | Out-Null
}

# The monkey-patch. Runs on every new document, polls for kcaseagt to appear,
# then wraps _daemonServiceRequest_Init, _daemonServiceRequest, and _daemonServiceRequest_http
# so we can see plaintext sendObj and the decrypted jsonObj. Also hooks the socket send/recv
# to see raw WSS frames with their own timestamps.
$hookJs = @'
(function () {
    if (window.__kcaseHooked) return;
    window.__kcaseHooked = true;

    var tag = function (label, obj) {
        try { console.log("__KCASE_HOOK__ " + label + " " + JSON.stringify(obj, null, 0)); }
        catch (e) { console.log("__KCASE_HOOK__ " + label + " <unstringifiable>"); }
    };

    // Intercept WebSocket send & messages regardless of patch timing
    var OrigWS = window.WebSocket;
    window.WebSocket = function (url, protocols) {
        var ws = protocols !== undefined ? new OrigWS(url, protocols) : new OrigWS(url);
        if (String(url).indexOf("127.0.0.1:8443") !== -1) {
            tag("WS_OPEN", { url: String(url) });
            var origSend = ws.send.bind(ws);
            ws.send = function (d) {
                tag("WS_SEND", { data: typeof d === "string" ? d : "<binary>" });
                return origSend(d);
            };
            ws.addEventListener("message", function (e) {
                tag("WS_RECV", { data: typeof e.data === "string" ? e.data : "<binary>" });
            });
            ws.addEventListener("close", function () { tag("WS_CLOSE", {}); });
        }
        return ws;
    };
    window.WebSocket.prototype = OrigWS.prototype;
    for (var k in OrigWS) { if (Object.prototype.hasOwnProperty.call(OrigWS, k)) window.WebSocket[k] = OrigWS[k]; }

    // Patch kcaseagt methods once they exist
    var attempts = 0;
    var poller = setInterval(function () {
        attempts++;
        if (typeof window.kcaseagt !== "undefined" && window.kcaseagt && typeof window.kcaseagt.init === "function") {
            clearInterval(poller);
            tag("KCASEAGT_READY", { apiNames: Object.keys(window.kcaseagt).filter(function (k) { return typeof window.kcaseagt[k] === "function"; }) });

            // Wrap every callable on kcaseagt to log its options (the plaintext sendObj input)
            var methods = [
                "checkInstallAgent", "init", "getCertList", "getCertListAdmin",
                "certLogin", "certLoginAsp", "genSignData", "verifySignData",
                "generateSymKeyIv", "blockCipher", "genEnvelopedData",
                "AsymmEncrypt", "secureEncrypt", "getVidInfo", "getVidInfoNSignedData",
                "deleteCert", "verifyCert", "changePassword", "verifyPassword",
                "hashData", "closeSecureChannel"
            ];
            methods.forEach(function (m) {
                var orig = window.kcaseagt[m];
                if (typeof orig !== "function") return;
                window.kcaseagt[m] = function (opts) {
                    try {
                        var shallow = {};
                        for (var k in opts) {
                            if (typeof opts[k] === "function") shallow[k] = "<fn>";
                            else shallow[k] = opts[k];
                        }
                        tag("CALL " + m, shallow);
                        // Wrap callbacks so we see outputs too
                        var wrapped = Object.assign({}, opts);
                        if (typeof opts.success === "function") {
                            wrapped.success = function () {
                                tag("CB " + m + ".success", Array.prototype.slice.call(arguments));
                                return opts.success.apply(this, arguments);
                            };
                        }
                        if (typeof opts.error === "function") {
                            wrapped.error = function () {
                                tag("CB " + m + ".error", Array.prototype.slice.call(arguments));
                                return opts.error.apply(this, arguments);
                            };
                        }
                        return orig.call(window.kcaseagt, wrapped);
                    } catch (e) {
                        tag("WRAP_ERR " + m, { err: String(e) });
                        return orig.apply(window.kcaseagt, arguments);
                    }
                };
            });
            tag("HOOKS_INSTALLED", { count: methods.length });
        } else if (attempts > 100) {
            clearInterval(poller);
            tag("HOOK_TIMEOUT", { attempts: attempts });
        }
    }, 100);
})();
'@

# Enable Page domain so our script runs on new docs
Send-Cmd -Method "Page.enable"
Send-Cmd -Method "Runtime.enable"
Send-Cmd -Method "Network.enable"
Send-Cmd -Method "Target.setAutoAttach" -Params @{ autoAttach = $true; waitForDebuggerOnStart = $false; flatten = $true }
Send-Cmd -Method "Target.setDiscoverTargets" -Params @{ discover = $true }

# Install on future loads + new targets
Send-Cmd -Method "Page.addScriptToEvaluateOnNewDocument" -Params @{ source = $hookJs }

# Also evaluate now so the current page gets hooked if it just loaded
Send-Cmd -Method "Runtime.evaluate" -Params @{ expression = $hookJs; awaitPromise = $false }

$sw = [System.IO.StreamWriter]::new($OutFile, $false, [Text.UTF8Encoding]::new($false))
$sw.AutoFlush = $true
Write-Host ""
Write-Host "Hook installed. Now in the Chrome window:"
Write-Host "  1. Hit Ctrl+F5 on the HIRA page (so the hook applies before JS loads)"
Write-Host "  2. Do the login normally"
Write-Host "  3. Ctrl+C here when finished"
Write-Host ""
Write-Host "Recording to: $OutFile"

$buffer = New-Object byte[] 65536
$hookEvents = 0
$wsEvents = 0
$totalEvents = 0

try {
    while ($ws.State -eq [System.Net.WebSockets.WebSocketState]::Open) {
        $ms = [System.IO.MemoryStream]::new()
        do {
            $seg = [ArraySegment[byte]]::new($buffer)
            $result = $ws.ReceiveAsync($seg, [Threading.CancellationToken]::None).GetAwaiter().GetResult()
            if ($result.MessageType -eq [System.Net.WebSockets.WebSocketMessageType]::Close) { throw "closed" }
            $ms.Write($buffer, 0, $result.Count)
        } while (-not $result.EndOfMessage)
        $msg = [System.Text.Encoding]::UTF8.GetString($ms.ToArray())
        $sw.WriteLine($msg)
        $totalEvents++

        # Route important events to console so user sees progress
        if ($msg -match '"method":"Runtime\.consoleAPICalled"' -and $msg -match '__KCASE_HOOK__') {
            $hookEvents++
            try {
                $obj = ConvertFrom-Json $msg -ErrorAction Stop
                $args = $obj.params.args
                if ($args -and $args.Length -gt 0) {
                    $first = $args[0].value
                    if ($first) {
                        $short = if ($first.Length -gt 180) { $first.Substring(0,180) + "..." } else { $first }
                        Write-Host "[HOOK] $short"
                    }
                }
            } catch {}
        } elseif ($msg -match '"method":"Network\.webSocketFrame(Sent|Received)"' -and $msg -match '127\.0\.0\.1:8443') {
            $wsEvents++
        }
    }
} finally {
    try { $sw.Close() } catch {}
    Write-Host ""
    Write-Host ("Done. {0} total events, {1} hook events, {2} ws frames. Saved to {3}" -f $totalEvents, $hookEvents, $wsEvents, $OutFile)
}
