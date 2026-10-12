#requires -Version 5.1
<#
.SYNOPSIS
  Attach to a Chrome instance running with --remote-debugging-port=9222 and
  capture all Network.webSocket* events (and everything else) to a JSONL file.

.DESCRIPTION
  Run this AFTER you've launched Chrome with launch-chrome.ps1.
  Navigate to https://ef.hira.or.kr/ in that Chrome window, then perform a login.
  Press Ctrl+C to stop capture.

.PARAMETER OutFile
  Path to write JSONL events. Default: C:\Temp\hira-capture.jsonl

.PARAMETER TargetPattern
  Regex to match target url to attach to. Default: hira.or.kr
#>
param(
    [string]$OutFile = "C:\Temp\hira-capture.jsonl",
    [string]$TargetPattern = "hira\.or\.kr"
)

$ErrorActionPreference = "Stop"

# Ensure out dir
$dir = Split-Path -Parent $OutFile
if ($dir -and -not (Test-Path $dir)) { New-Item -ItemType Directory -Path $dir -Force | Out-Null }

# Find the best target
Write-Host "Locating CDP targets on http://127.0.0.1:9222/json/list ..."
$targets = $null
for ($i = 0; $i -lt 10; $i++) {
    try {
        $targets = Invoke-RestMethod -Uri "http://127.0.0.1:9222/json/list" -TimeoutSec 2
        break
    } catch {
        Start-Sleep -Seconds 1
    }
}
if (-not $targets) {
    Write-Error "Could not reach Chrome CDP on port 9222. Launch Chrome with --remote-debugging-port=9222 first."
    exit 1
}

# Prefer a target matching the hira pattern, else the first page target
$target = $targets | Where-Object { $_.type -eq "page" -and $_.url -match $TargetPattern } | Select-Object -First 1
if (-not $target) {
    $target = $targets | Where-Object { $_.type -eq "page" } | Select-Object -First 1
}
if (-not $target) {
    Write-Error "No usable CDP page target found."
    exit 1
}

Write-Host "Attaching to target: $($target.title) [$($target.url)]"
Write-Host "WebSocket debugger URL: $($target.webSocketDebuggerUrl)"

$ws = [System.Net.WebSockets.ClientWebSocket]::new()
$ws.Options.KeepAliveInterval = [TimeSpan]::FromSeconds(30)
$uri = [Uri]::new($target.webSocketDebuggerUrl)
$ws.ConnectAsync($uri, [Threading.CancellationToken]::None).GetAwaiter().GetResult()
Write-Host "Connected."

$msgId = 0
function Send-Cmd {
    param([string]$Method, $Params)
    $script:msgId++
    $obj = [ordered]@{ id = $script:msgId; method = $Method }
    if ($Params) { $obj.params = $Params }
    $json = $obj | ConvertTo-Json -Compress -Depth 20
    $bytes = [System.Text.Encoding]::UTF8.GetBytes($json)
    $seg = [ArraySegment[byte]]::new($bytes)
    $ws.SendAsync($seg, [System.Net.WebSockets.WebSocketMessageType]::Text, $true, [Threading.CancellationToken]::None).GetAwaiter().GetResult()
}

Send-Cmd -Method "Network.enable"
Send-Cmd -Method "Page.enable"
Send-Cmd -Method "Target.setAutoAttach" -Params @{ autoAttach = $true; waitForDebuggerOnStart = $false; flatten = $true }
Send-Cmd -Method "Target.setDiscoverTargets" -Params @{ discover = $true }

$sw = [System.IO.StreamWriter]::new($OutFile, $false, [Text.UTF8Encoding]::new($false))
$sw.AutoFlush = $true
Write-Host ""
Write-Host "Recording to: $OutFile"
Write-Host "Now do the HIRA login in the Chrome window."
Write-Host "Press Ctrl+C when done."
Write-Host ""

$buffer = New-Object byte[] 65536
$totalFrames = 0
$wsFrames = 0

try {
    while ($ws.State -eq [System.Net.WebSockets.WebSocketState]::Open) {
        $ms = [System.IO.MemoryStream]::new()
        do {
            $seg = [ArraySegment[byte]]::new($buffer)
            $result = $ws.ReceiveAsync($seg, [Threading.CancellationToken]::None).GetAwaiter().GetResult()
            if ($result.MessageType -eq [System.Net.WebSockets.WebSocketMessageType]::Close) {
                throw "CDP socket closed"
            }
            $ms.Write($buffer, 0, $result.Count)
        } while (-not $result.EndOfMessage)

        $msg = [System.Text.Encoding]::UTF8.GetString($ms.ToArray())
        $sw.WriteLine($msg)
        $totalFrames++

        # Live feedback for WebSocket-related events & target auto-attach
        if ($msg -match '"method":"(Network\.webSocket\w+|Target\.attachedToTarget|Target\.targetCreated)"') {
            $wsFrames++
            try {
                $obj = ConvertFrom-Json $msg -ErrorAction Stop
                $detail = ""
                switch ($obj.method) {
                    "Network.webSocketCreated" { $detail = $obj.params.url }
                    "Network.webSocketFrameSent" { $detail = "SENT  len=$($obj.params.response.payloadData.Length)  $($obj.params.response.payloadData.Substring(0, [Math]::Min(120,$obj.params.response.payloadData.Length)))" }
                    "Network.webSocketFrameReceived" { $detail = "RECV  len=$($obj.params.response.payloadData.Length)  $($obj.params.response.payloadData.Substring(0, [Math]::Min(120,$obj.params.response.payloadData.Length)))" }
                    "Network.webSocketClosed" { $detail = "closed" }
                    "Target.attachedToTarget" { $detail = "attached $($obj.params.targetInfo.type) $($obj.params.targetInfo.url)" }
                    "Target.targetCreated" { $detail = "new $($obj.params.targetInfo.type) $($obj.params.targetInfo.url)" }
                }
                Write-Host ("[{0:HH:mm:ss}] {1} {2}" -f (Get-Date), $obj.method, $detail)
            } catch { }
        }

        if ($totalFrames % 500 -eq 0) {
            Write-Host ("... {0} total events, {1} ws/target events" -f $totalFrames, $wsFrames)
        }
    }
} finally {
    try { $sw.Close() } catch {}
    try { $ws.CloseAsync([System.Net.WebSockets.WebSocketCloseStatus]::NormalClosure, "done", [Threading.CancellationToken]::None).GetAwaiter().GetResult() } catch {}
    Write-Host ""
    Write-Host ("Done. Wrote {0} events ({1} ws/target) to {2}" -f $totalFrames, $wsFrames, $OutFile)
}
