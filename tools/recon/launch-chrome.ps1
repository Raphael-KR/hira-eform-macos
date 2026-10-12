#requires -Version 5.1
<#
.SYNOPSIS
  Launch a fresh Chrome window with remote debugging enabled on port 9222.
  Uses an isolated profile so it won't touch your normal browsing.

  After this, run capture-cdp.ps1 in another PowerShell window to attach.
#>
param(
    [string]$UserDataDir = "C:\Temp\chrome-cdp-profile",
    [string]$Url = "https://ef.hira.or.kr/",
    [int]$Port = 9222
)

$chrome = "C:\Program Files\Google\Chrome\Application\chrome.exe"
if (-not (Test-Path $chrome)) {
    $chrome = "C:\Program Files (x86)\Google\Chrome\Application\chrome.exe"
}
if (-not (Test-Path $chrome)) { Write-Error "Chrome not found"; exit 1 }

if (-not (Test-Path $UserDataDir)) { New-Item -ItemType Directory -Path $UserDataDir -Force | Out-Null }

$args = @(
    "--remote-debugging-port=$Port",
    "--user-data-dir=$UserDataDir",
    "--no-first-run",
    "--no-default-browser-check",
    # Localhost remote debugging only
    "--remote-allow-origins=http://127.0.0.1:$Port",
    $Url
)

Write-Host "Launching: $chrome $($args -join ' ')"
Start-Process -FilePath $chrome -ArgumentList $args
Start-Sleep -Seconds 2
try {
    $info = Invoke-RestMethod -Uri "http://127.0.0.1:$Port/json/version" -TimeoutSec 3
    Write-Host ""
    Write-Host "Chrome is up. Browser: $($info.Browser)  Protocol: $($info.'Protocol-Version')"
    Write-Host "CDP URL: $($info.webSocketDebuggerUrl)"
    Write-Host ""
    Write-Host "Next: run .\capture-cdp.ps1 in another PowerShell window, then do the login."
} catch {
    Write-Warning "Chrome launched but CDP endpoint not responding yet. Wait a few seconds and retry."
}
