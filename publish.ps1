<#
.SYNOPSIS
    Creates a GitHub Release for this repo and attaches the built exe.

.DESCRIPTION
    Uses the GitHub token stored in Git Credential Manager (the same one git push uses).
    Run after building the exe:
        pyinstaller --noconsole --onefile --name MachineStatusMonitor --add-data "static;static" server.py

.EXAMPLE
    .\publish.ps1 -Version 1.0.0
    .\publish.ps1 -Version 0.0.2 -Prerelease
#>
param(
    [Parameter(Mandatory = $true)][string]$Version,
    [string]$ExePath   = "dist\MachineStatusMonitor.exe",
    [string]$AssetName = "MachineStatusMonitor.exe",
    [switch]$Prerelease
)

$ErrorActionPreference = "Stop"

$Repo = "Sean-Robinson-15/machine-status-monitor"

if (-not (Test-Path $ExePath)) {
    throw "Exe not found: $ExePath (build it first, see .SYNOPSIS)"
}

# Pull the GitHub token from Git Credential Manager (non-interactive; cached by git).
$cred  = "protocol=https`nhost=github.com`n" | git credential fill
$token = ($cred | Where-Object { $_ -match '^password=' } | ForEach-Object { $_ -replace '^password=' })
if (-not $token) {
    throw "No GitHub token found in Git Credential Manager. Run 'git push' once first."
}

$headers = @{
    "Authorization" = "Bearer $token"
    "Accept"        = "application/vnd.github+json"
}

$tag = "v$Version"

# Reuse an existing release if the tag is already published (idempotent).
try {
    $release = Invoke-RestMethod -Uri "https://api.github.com/repos/$Repo/releases/tags/$tag" -Headers $headers
    Write-Host "Reusing existing release $tag ..." -ForegroundColor Cyan
} catch {
    $body = @{
        tag_name   = $tag
        name       = $tag
        body       = "Machine Status Monitor $Version`n`n" +
                     "- Single-file Windows executable (no Python required)`n" +
                     "- Runs silently with no console window`n" +
                     "- Double-click, then open http://localhost:5000"
        draft      = $false
        prerelease = [bool]$Prerelease
    } | ConvertTo-Json
    Write-Host "Creating release $tag ..." -ForegroundColor Cyan
    $release = Invoke-RestMethod -Uri "https://api.github.com/repos/$Repo/releases" `
        -Headers $headers -Method Post -Body $body -ContentType "application/json"
}

# upload_url is a template like ".../assets{?name,label}" — strip the template,
# put the asset name in the query string, and send the file as multipart.
$baseUrl   = $release.upload_url -replace '\{.*$',''
$uploadUrl = $baseUrl + "?name=$AssetName"

Write-Host "Uploading $AssetName ($([math]::Round((Get-Item $ExePath).Length/1MB,2)) MB) ..." -ForegroundColor Cyan
$curlOut = & curl.exe -sS -X POST $uploadUrl `
    -H "Authorization: Bearer $token" `
    -F "file=@$ExePath;type=application/octet-stream"
if ($LASTEXITCODE -ne 0) {
    throw "Upload failed (curl exit $LASTEXITCODE): $curlOut"
}
$asset = $curlOut | ConvertFrom-Json

Write-Host ""
Write-Host "Done!" -ForegroundColor Green
Write-Host "Release: $($release.html_url)"
Write-Host "Asset:   $($asset.name) ($([math]::Round($asset.size/1MB,2)) MB)"
