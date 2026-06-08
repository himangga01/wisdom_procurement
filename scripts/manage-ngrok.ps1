param(
  [ValidateSet("start", "stop", "status")]
  [string]$Action = "status",
  [int]$BackendPort = 18111,
  [int]$FrontendPort = 5199,
  [int]$BackendNgrokApiPort = 4040,
  [int]$FrontendNgrokApiPort = 4041
)

$ErrorActionPreference = "Stop"

try {
  $utf8NoBom = New-Object System.Text.UTF8Encoding($false)
  [Console]::InputEncoding = $utf8NoBom
  [Console]::OutputEncoding = $utf8NoBom
  $OutputEncoding = $utf8NoBom
} catch {}
$env:PYTHONIOENCODING = "utf-8"
$env:PYTHONUTF8 = "1"

$Root = Split-Path -Parent $PSScriptRoot
$BackendDir = Join-Path $Root "backend"
$FrontendDir = Join-Path $Root "frontend"
$TempDir = Join-Path $Root "temp"
$StatusPath = Join-Path $TempDir "ngrok.status.json"
$BackendNgrokLogPath = Join-Path $TempDir "ngrok.backend.log"
$FrontendNgrokLogPath = Join-Path $TempDir "ngrok.frontend.log"
$BackendLocalUrl = "http://127.0.0.1:$BackendPort"
$FrontendLocalUrl = "http://127.0.0.1:$FrontendPort"

function Ensure-TempDir {
  New-Item -ItemType Directory -Force $TempDir | Out-Null
}

function Read-NgrokStatus {
  if (Test-Path $StatusPath) {
    try {
      return Get-Content $StatusPath -Raw -Encoding UTF8 | ConvertFrom-Json
    } catch {
      return $null
    }
  }
  return $null
}

function Write-NgrokStatus($Payload) {
  Ensure-TempDir
  $json = $Payload | ConvertTo-Json -Depth 6
  $encoding = $utf8NoBom
  if (!$encoding) {
    $encoding = New-Object System.Text.UTF8Encoding($false)
  }
  [System.IO.File]::WriteAllText($StatusPath, $json, $encoding)
}

function Remove-NgrokStatus {
  if (Test-Path $StatusPath) {
    Remove-Item $StatusPath -Force -ErrorAction SilentlyContinue
  }
}

function Stop-ProcessIfManaged($ProcessId) {
  if (!$ProcessId) { return }
  $processIds = Get-ManagedProcessIds $ProcessId
  [array]::Reverse($processIds)
  foreach ($managedProcessId in $processIds) {
    try {
      Stop-Process -Id ([int]$managedProcessId) -Force -ErrorAction SilentlyContinue
    } catch {}
  }
}

function Get-ManagedProcessIds($ProcessId) {
  if (!$ProcessId) { return @() }
  $rootPid = [int]$ProcessId
  $ids = New-Object System.Collections.Generic.List[int]
  $queue = New-Object System.Collections.Generic.Queue[int]
  $ids.Add($rootPid)
  $queue.Enqueue($rootPid)
  try {
    $processes = Get-CimInstance Win32_Process -ErrorAction SilentlyContinue
    while ($queue.Count -gt 0) {
      $currentPid = $queue.Dequeue()
      foreach ($child in ($processes | Where-Object { $_.ParentProcessId -eq $currentPid })) {
        $childPid = [int]$child.ProcessId
        if (!$ids.Contains($childPid)) {
          $ids.Add($childPid)
          $queue.Enqueue($childPid)
        }
      }
    }
  } catch {}
  return $ids.ToArray()
}

function Stop-NgrokManaged {
  $status = Read-NgrokStatus
  if ($status) {
    Stop-ProcessIfManaged $status.backend_ngrok_pid
    Stop-ProcessIfManaged $status.frontend_ngrok_pid
    Stop-ProcessIfManaged $status.backend_pid
    Stop-ProcessIfManaged $status.frontend_pid
  }
  Remove-NgrokStatus
  Remove-Item $BackendNgrokLogPath,$FrontendNgrokLogPath -Force -ErrorAction SilentlyContinue
}

function Assert-NgrokCli {
  $cmd = Get-Command ngrok -ErrorAction SilentlyContinue
  if (!$cmd) {
    throw "ngrok CLI was not found. Install ngrok and run 'ngrok config add-authtoken <token>' first."
  }
}

function Test-NgrokAuthConfigured {
  if ($env:NGROK_AUTHTOKEN) { return $true }
  $candidates = @(
    (Join-Path $env:USERPROFILE "AppData\Local\ngrok\ngrok.yml"),
    (Join-Path $env:USERPROFILE ".ngrok2\ngrok.yml")
  )
  foreach ($candidate in $candidates) {
    if ((Test-Path $candidate) -and ((Get-Content $candidate -Raw -ErrorAction SilentlyContinue) -match "authtoken")) {
      return $true
    }
  }
  return $false
}

function Assert-PortAvailableOrManaged($Port, $ManagedPid) {
  $listeners = @()
  $managedIds = Get-ManagedProcessIds $ManagedPid
  try {
    $listeners = Get-NetTCPConnection -State Listen -LocalPort $Port -ErrorAction SilentlyContinue |
      Select-Object -ExpandProperty OwningProcess -Unique
  } catch {}
  foreach ($listener in $listeners) {
    if ($ManagedPid -and $managedIds.Contains([int]$listener)) {
      continue
    }
    throw "Port $Port is already in use by process $listener and is not managed by scripts/manage-ngrok.ps1."
  }
}

function Wait-HttpOk($Url, $Attempts = 80, $SleepMs = 300) {
  for ($i = 0; $i -lt $Attempts; $i++) {
    try {
      $response = Invoke-WebRequest -Uri $Url -UseBasicParsing -TimeoutSec 2
      if ($response.StatusCode -ge 200 -and $response.StatusCode -lt 500) {
        return $true
      }
    } catch {}
    Start-Sleep -Milliseconds $SleepMs
  }
  return $false
}

function Get-NgrokPublicUrl($LogPath, $LocalPort) {
  for ($i = 0; $i -lt 80; $i++) {
    if (Test-Path $LogPath) {
      try {
        $raw = Get-Content $LogPath -Raw -Encoding UTF8 -ErrorAction SilentlyContinue
        foreach ($line in ($raw -split "`r?`n")) {
          if (!$line.Trim()) { continue }
          try {
            $entry = $line | ConvertFrom-Json
            if ($entry.url -like "https://*" -and $entry.addr -like "*:$LocalPort*") {
              return $entry.url
            }
          } catch {}
        }
        if ($raw -match '"url"\s*:\s*"(https://[^"]+)"') {
          return $matches[1]
        }
      } catch {}
    }
    Start-Sleep -Milliseconds 300
  }
  throw "Could not read ngrok public URL for local port $LocalPort."
}

function Start-NgrokProcess($LocalPort, $LogPath) {
  Remove-Item $LogPath -Force -ErrorAction SilentlyContinue
  $args = @(
    "http",
    "http://127.0.0.1:$LocalPort",
    "--log",
    $LogPath,
    "--log-format",
    "json"
  )
  return Start-Process -FilePath "ngrok" -ArgumentList $args -WindowStyle Hidden -PassThru
}

function Start-Backend {
  $env:APP_PORT = [string]$BackendPort
  return Start-Process -FilePath "py" -ArgumentList @("-3.13", "-m", "app.main") -WorkingDirectory $BackendDir -WindowStyle Hidden -PassThru
}

function Start-Frontend($BackendPublicUrl) {
  $env:VITE_API_BASE_URL = $BackendPublicUrl
  $env:VITE_ALLOW_NGROK_HOSTS = "1"
  return Start-Process -FilePath "cmd.exe" -ArgumentList @("/c", "npm run dev -- --host 127.0.0.1 --port $FrontendPort") -WorkingDirectory $FrontendDir -WindowStyle Hidden -PassThru
}

function Show-Status {
  $status = Read-NgrokStatus
  if (!$status) {
    [ordered]@{
      enabled = $false
      provider = "ngrok"
      status_file = $StatusPath
    } | ConvertTo-Json -Depth 4
    return
  }
  $status | ConvertTo-Json -Depth 6
}

if ($Action -eq "status") {
  Show-Status
  exit 0
}

if ($Action -eq "stop") {
  Stop-NgrokManaged
  Show-Status
  exit 0
}

Assert-NgrokCli
if (!(Test-NgrokAuthConfigured)) {
  throw "ngrok auth token was not found. Run 'ngrok config add-authtoken <token>' or set NGROK_AUTHTOKEN."
}

$previous = Read-NgrokStatus
Assert-PortAvailableOrManaged $BackendPort ($previous.backend_pid)
Assert-PortAvailableOrManaged $FrontendPort ($previous.frontend_pid)

Stop-NgrokManaged
Ensure-TempDir

$backend = Start-Backend
if (!(Wait-HttpOk "$BackendLocalUrl/health")) {
  Stop-ProcessIfManaged $backend.Id
  throw "Backend did not become ready at $BackendLocalUrl."
}

$backendNgrok = Start-NgrokProcess $BackendPort $BackendNgrokLogPath
$backendPublicUrl = Get-NgrokPublicUrl $BackendNgrokLogPath $BackendPort

$frontend = Start-Frontend $backendPublicUrl
if (!(Wait-HttpOk $FrontendLocalUrl)) {
  Stop-ProcessIfManaged $backendNgrok.Id
  Stop-ProcessIfManaged $backend.Id
  Stop-ProcessIfManaged $frontend.Id
  throw "Frontend did not become ready at $FrontendLocalUrl."
}

$frontendNgrok = Start-NgrokProcess $FrontendPort $FrontendNgrokLogPath
$frontendPublicUrl = Get-NgrokPublicUrl $FrontendNgrokLogPath $FrontendPort

$payload = [ordered]@{
  enabled = $true
  provider = "ngrok"
  backend_public_url = $backendPublicUrl
  frontend_public_url = $frontendPublicUrl
  backend_local_url = $BackendLocalUrl
  frontend_local_url = $FrontendLocalUrl
  backend_port = $BackendPort
  frontend_port = $FrontendPort
  backend_ngrok_api_port = $BackendNgrokApiPort
  frontend_ngrok_api_port = $FrontendNgrokApiPort
  backend_ngrok_log_path = $BackendNgrokLogPath
  frontend_ngrok_log_path = $FrontendNgrokLogPath
  backend_pid = $backend.Id
  frontend_pid = $frontend.Id
  backend_ngrok_pid = $backendNgrok.Id
  frontend_ngrok_pid = $frontendNgrok.Id
  updated_at = (Get-Date).ToString("yyyy-MM-dd HH:mm:ss zzz")
  warnings = @("External URLs expose this local app while tunnels are running.", "Secrets and raw env values are not stored in this file.")
}
Write-NgrokStatus $payload
Show-Status
