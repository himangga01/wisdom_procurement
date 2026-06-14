param(
  [string]$Seed = "",
  [switch]$SkipPreflight,
  [switch]$DryRun,
  [switch]$Headed
)

$ErrorActionPreference = "Stop"
$repoRoot = Split-Path -Parent $PSScriptRoot
$frontendDir = Join-Path $repoRoot "frontend"
$serverScript = Join-Path $PSScriptRoot "manage-servers.ps1"

Write-Host "[demo-video] Starting local backend/frontend servers"
powershell -ExecutionPolicy Bypass -File $serverScript -Action start | Write-Host

Push-Location $frontendDir
try {
  $recordArgs = @("run", "demo:record", "--")
  if ($Seed) {
    $recordArgs += @("--seed", $Seed)
  }
  if ($SkipPreflight) {
    $recordArgs += "--skip-preflight"
  }
  if ($DryRun) {
    $recordArgs += "--dry-run"
  }
  if ($Headed) {
    $recordArgs += "--headed"
  }

  Write-Host "[demo-video] Recording demo flow"
  & npm @recordArgs

  if (-not $DryRun) {
    Write-Host "[demo-video] Rendering MP4"
    & npm run demo:render

    Write-Host "[demo-video] Inspecting MP4"
    & npm run demo:inspect
  }
} finally {
  Pop-Location
}

Write-Host "[demo-video] Done. See artifacts/demo-video/latest-report.json"
