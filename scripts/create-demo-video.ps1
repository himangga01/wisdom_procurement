param(
  [string]$Seed = "",
  [string]$Mode = "full-workflow-demo",
  [string]$NaraKeyword = "전자칠판",
  [string]$NaraBusinessType = "goods",
  [int]$EvidenceFileLimit = 4,
  [string]$Scene = "",
  [switch]$Segments,
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
  if ($Segments) {
    Write-Host "[demo-video] demo:segments mode enabled (--segments)"
    $segmentGroups = @(
      "intro,corporations,nara-board,saved-notice",
      "basis-documents,notice-comparison,judgment-runs",
      "contracts,operations,operation-runs"
    )
    $segmentMp4s = @()
    foreach ($segment in $segmentGroups) {
      $recordArgs = @(
        "run",
        "demo:record",
        "--",
        "--mode", $Mode,
        "--scene", $segment,
        "--nara-keyword", $NaraKeyword,
        "--nara-business-type", $NaraBusinessType,
        "--evidence-file-limit", [string]$EvidenceFileLimit
      )
      if ($Seed) {
        $recordArgs += @("--seed", ($Seed + "-" + (($segmentMp4s.Count + 1).ToString("00"))))
      }
      if ($SkipPreflight -or $segmentMp4s.Count -gt 0) {
        $recordArgs += "--skip-preflight"
      }
      if ($DryRun) {
        $recordArgs += "--dry-run"
      }
      if ($Headed) {
        $recordArgs += "--headed"
      }

      Write-Host "[demo-video] Recording segment: $segment"
      & npm @recordArgs

      if (-not $DryRun) {
        $segmentOutput = Join-Path $repoRoot ("artifacts\demo-video\segments\service-demo-segment-" + (($segmentMp4s.Count + 1).ToString("00")) + ".mp4")
        New-Item -ItemType Directory -Force (Split-Path -Parent $segmentOutput) | Out-Null
        & npm run demo:render -- --output $segmentOutput
        $segmentMp4s += $segmentOutput
      }
    }

    if (-not $DryRun) {
      $ffmpeg = Join-Path $frontendDir "node_modules\ffmpeg-static\ffmpeg.exe"
      if (!(Test-Path $ffmpeg)) {
        throw "ffmpeg-static binary was not found at $ffmpeg"
      }
      $concatFile = Join-Path $repoRoot "artifacts\demo-video\segments\concat-list.txt"
      $concatLines = $segmentMp4s | ForEach-Object { "file '$($_.Replace('\', '/'))'" }
      [System.IO.File]::WriteAllLines($concatFile, $concatLines, [System.Text.UTF8Encoding]::new($false))
      $outputPath = Join-Path $repoRoot "artifacts\demo-video\service-demo-full-workflow.mp4"
      & $ffmpeg -y -f concat -safe 0 -i $concatFile -c copy -movflags +faststart $outputPath
      & npm run demo:inspect -- --input $outputPath --seed full-workflow
    }
    Write-Host "[demo-video] Done. See artifacts/demo-video/service-demo-full-workflow.mp4"
    return
  }

  $recordArgs = @(
    "run",
    "demo:record",
    "--",
    "--mode", $Mode,
    "--nara-keyword", $NaraKeyword,
    "--nara-business-type", $NaraBusinessType,
    "--evidence-file-limit", [string]$EvidenceFileLimit
  )
  if ($Seed) {
    $recordArgs += @("--seed", $Seed)
  }
  if ($Scene) {
    $recordArgs += @("--scene", $Scene)
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
