param(
  [ValidateSet("start", "stop", "restart", "status")]
  [string]$Action = "status",
  [int]$BackendPort = 18111,
  [int]$FrontendPort = 5199
)

$ErrorActionPreference = "Stop"

$Root = Split-Path -Parent $PSScriptRoot
$BackendDir = Join-Path $Root "backend"
$FrontendDir = Join-Path $Root "frontend"
$TempDir = Join-Path $Root "temp"
$StatusPath = Join-Path $TempDir "servers.status.json"
$BackendUrl = "http://127.0.0.1:$BackendPort"
$FrontendUrl = "http://127.0.0.1:$FrontendPort"
$Python313Exe = $null

function Ensure-Directories {
  New-Item -ItemType Directory -Force $TempDir | Out-Null
}

function Ensure-EnvFiles {
  $backendEnv = Join-Path $BackendDir ".env"
  $backendExample = Join-Path $BackendDir ".env.example"
  $frontendEnv = Join-Path $FrontendDir ".env"
  $frontendExample = Join-Path $FrontendDir ".env.example"

  if (!(Test-Path $backendEnv) -and (Test-Path $backendExample)) {
    Copy-Item $backendExample $backendEnv
  }
  if (!(Test-Path $frontendEnv) -and (Test-Path $frontendExample)) {
    Copy-Item $frontendExample $frontendEnv
  }
}

function Read-StatusFile {
  if (Test-Path $StatusPath) {
    try {
      return Get-Content $StatusPath -Raw | ConvertFrom-Json
    } catch {
      return $null
    }
  }
  return $null
}

function Write-StatusFile($BackendPid, $FrontendPid, $BackendReady, $FrontendReady) {
  $payload = [ordered]@{
    backend_pid = $BackendPid
    frontend_pid = $FrontendPid
    backend_ready = $BackendReady
    frontend_ready = $FrontendReady
    backend_python = $script:Python313Exe
    backend_url = $BackendUrl
    frontend_url = $FrontendUrl
    backend_port = $BackendPort
    frontend_port = $FrontendPort
    updated_at = (Get-Date).ToString("yyyy-MM-dd HH:mm:ss zzz")
  }
  $payload | ConvertTo-Json -Compress | Set-Content -Encoding UTF8 $StatusPath
}

function Remove-StatusFile {
  if (Test-Path $StatusPath) {
    Remove-Item $StatusPath -Force -ErrorAction SilentlyContinue
  }
}

function Test-HttpOk($Url) {
  try {
    $code = & curl.exe --silent --output NUL --write-out "%{http_code}" $Url
    return $code -eq "200"
  } catch {
    return $false
  }
}

function Test-BackendHealth {
  try {
    $health = Invoke-RestMethod -Uri "$BackendUrl/health" -TimeoutSec 2
    return $health.status -eq "ok"
  } catch {
    return $false
  }
}

function Wait-UntilReady {
  param(
    [scriptblock]$Probe,
    [int]$Attempts = 80,
    [int]$SleepMs = 300
  )

  for ($i = 0; $i -lt $Attempts; $i++) {
    if (& $Probe) {
      return $true
    }
    Start-Sleep -Milliseconds $SleepMs
  }
  return $false
}

function Get-Python313Executable {
  $candidates = New-Object System.Collections.Generic.List[string]

  try {
    $resolved = & py -3.13 -c "import sys; print(sys.executable)" 2>$null
    if ($LASTEXITCODE -eq 0 -and $resolved) {
      $candidates.Add(($resolved | Select-Object -First 1).Trim())
    }
  } catch {}

  $candidates.Add("C:\Python313\python.exe")

  foreach ($candidate in $candidates) {
    if ($candidate -and (Test-Path $candidate)) {
      return (Resolve-Path $candidate).Path
    }
  }

  throw "Python 3.13 runtime was not found. Install Python 3.13.13 and make sure 'py -3.13' works."
}

function Get-ProjectProcessCandidates {
  $status = Read-StatusFile
  $pids = New-Object System.Collections.Generic.List[int]

  if ($status) {
    if ($status.backend_pid) { $pids.Add([int]$status.backend_pid) }
    if ($status.frontend_pid) { $pids.Add([int]$status.frontend_pid) }
  }

  try {
    $listening = Get-NetTCPConnection -State Listen -ErrorAction SilentlyContinue |
      Where-Object { $_.LocalPort -in @($BackendPort, $FrontendPort) } |
      Select-Object -ExpandProperty OwningProcess -Unique
    foreach ($procId in $listening) {
      if ($procId) { $pids.Add([int]$procId) }
    }
  } catch {}

  try {
    $projectProcesses = Get-CimInstance Win32_Process -ErrorAction SilentlyContinue |
      Where-Object {
        $_.Name -in @("cmd.exe", "node.exe", "python.exe", "py.exe") -and
        $_.CommandLine -like "*D:\project\wisdom_procurement*"
      } |
      Select-Object -ExpandProperty ProcessId -Unique

    foreach ($procId in $projectProcesses) {
      if ($procId -and $procId -ne $PID) { $pids.Add([int]$procId) }
    }
  } catch {}

  return $pids | Sort-Object -Unique
}

function Stop-ManagedServers {
  $targets = Get-ProjectProcessCandidates
  foreach ($procId in $targets) {
    Stop-Process -Id $procId -Force -ErrorAction SilentlyContinue
  }
  Remove-StatusFile
}

function Start-ManagedServers {
  Ensure-Directories
  Ensure-EnvFiles

  Stop-ManagedServers
  $script:Python313Exe = Get-Python313Executable

  $runId = Get-Date -Format "yyyyMMddHHmmss"
  $backendOutLog = Join-Path $TempDir "backend.$runId.out.log"
  $backendErrLog = Join-Path $TempDir "backend.$runId.err.log"
  $frontendOutLog = Join-Path $TempDir "frontend.$runId.out.log"
  $frontendErrLog = Join-Path $TempDir "frontend.$runId.err.log"

  $backendCmd = 'set "APP_PORT=' + $BackendPort + '" && set "PYTHONUTF8=1" && cd /d "' + $BackendDir + '" && "' + $script:Python313Exe + '" -m app.main'
  $frontendCmd = 'set "VITE_API_BASE_URL=' + $BackendUrl + '" && cd /d "' + $FrontendDir + '" && npm run dev -- --host 127.0.0.1 --port ' + $FrontendPort

  $backendProcess = Start-Process -FilePath "cmd.exe" -ArgumentList "/c", $backendCmd -PassThru -WindowStyle Hidden -RedirectStandardOutput $backendOutLog -RedirectStandardError $backendErrLog
  $frontendProcess = Start-Process -FilePath "cmd.exe" -ArgumentList "/c", $frontendCmd -PassThru -WindowStyle Hidden -RedirectStandardOutput $frontendOutLog -RedirectStandardError $frontendErrLog

  $backendReady = Wait-UntilReady -Probe { Test-BackendHealth }
  $frontendReady = Wait-UntilReady -Probe { Test-HttpOk $FrontendUrl }

  Write-StatusFile -BackendPid $backendProcess.Id -FrontendPid $frontendProcess.Id -BackendReady $backendReady -FrontendReady $frontendReady

  if (-not $backendReady -or -not $frontendReady) {
    $frontendErr = ""
    $backendErr = ""
    if (Test-Path $frontendErrLog) { $frontendErr = (Get-Content $frontendErrLog -Raw).Trim() }
    if (Test-Path $backendErrLog) { $backendErr = (Get-Content $backendErrLog -Raw).Trim() }
    throw ("Server start failed. backend_ready=" + $backendReady + ", frontend_ready=" + $frontendReady + "`nbackend_err=" + $backendErr + "`nfrontend_err=" + $frontendErr)
  }

  return Read-StatusFile
}

function Get-ManagedStatus {
  $status = Read-StatusFile

  if (-not $status) {
    return [ordered]@{
      backend_running = $false
      frontend_running = $false
      backend_url = $BackendUrl
      frontend_url = $FrontendUrl
      message = "No status file found"
    }
  }

  return [ordered]@{
    backend_pid = $status.backend_pid
    frontend_pid = $status.frontend_pid
    backend_running = (Test-BackendHealth)
    frontend_running = (Test-HttpOk $status.frontend_url)
    backend_url = $status.backend_url
    frontend_url = $status.frontend_url
    backend_port = $status.backend_port
    frontend_port = $status.frontend_port
    backend_python = $status.backend_python
    updated_at = $status.updated_at
  }
}

Ensure-Directories

switch ($Action) {
  "start" {
    $result = Start-ManagedServers
    Write-Output ($result | ConvertTo-Json -Compress)
  }
  "stop" {
    Stop-ManagedServers
    $result = [ordered]@{
      stopped = $true
      backend_port = $BackendPort
      frontend_port = $FrontendPort
    }
    Write-Output ($result | ConvertTo-Json -Compress)
  }
  "restart" {
    Stop-ManagedServers
    $result = Start-ManagedServers
    Write-Output ($result | ConvertTo-Json -Compress)
  }
  "status" {
    $result = Get-ManagedStatus
    Write-Output ($result | ConvertTo-Json -Compress)
  }
}
