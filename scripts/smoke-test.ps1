$ErrorActionPreference = "Stop"

$root = Split-Path -Parent $PSScriptRoot
$backendDir = Join-Path $root "backend"
$frontendDir = Join-Path $root "frontend"
$tempDir = Join-Path $root "temp"
$samplePdf = Join-Path $tempDir "smoke-sample.pdf"
$backendPort = 18111
$frontendPort = 5199
$backendBase = "http://127.0.0.1:$backendPort"
$frontendBase = "http://127.0.0.1:$frontendPort"
$manageScript = Join-Path $PSScriptRoot "manage-servers.ps1"
$pythonExe = Join-Path $backendDir ".venv\Scripts\python.exe"
$logPath = Join-Path $tempDir "smoke-test.log"

if (!(Test-Path $pythonExe)) {
  $pythonExe = Join-Path $backendDir ".venv313\Scripts\python.exe"
}

New-Item -ItemType Directory -Force $tempDir | Out-Null
Set-Content -Path $logPath -Value "smoke_start=$(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')" -Encoding UTF8

function Write-SmokeLog($Message) {
  Add-Content -Path $logPath -Value ("$(Get-Date -Format 'HH:mm:ss') " + $Message) -Encoding UTF8
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
    $health = Invoke-RestMethod -Uri "$backendBase/health" -TimeoutSec 2
    return $health.status -eq "ok"
  } catch {
    return $false
  }
}

function Wait-UntilReady {
  param(
    [scriptblock]$Probe,
    [string]$Name,
    [int]$Attempts = 80,
    [int]$SleepMs = 300
  )

  for ($i = 0; $i -lt $Attempts; $i++) {
    if (& $Probe) {
      Write-SmokeLog "$Name ready"
      return
    }
    Start-Sleep -Milliseconds $SleepMs
  }

  throw "$Name did not become ready."
}

function Stop-SmokeServers {
  powershell -ExecutionPolicy Bypass -File $manageScript -Action stop -BackendPort $backendPort -FrontendPort $frontendPort | Out-Null
}

try {
  Write-SmokeLog "stopping_existing_servers"
  Stop-SmokeServers

  if (!(Test-Path $pythonExe)) {
    throw "Backend Python executable was not found. Expected .venv or .venv313 under backend."
  }

  $runId = Get-Date -Format "yyyyMMddHHmmss"
  $backendOutLog = Join-Path $tempDir "smoke-backend.$runId.out.log"
  $backendErrLog = Join-Path $tempDir "smoke-backend.$runId.err.log"
  $frontendOutLog = Join-Path $tempDir "smoke-frontend.$runId.out.log"
  $frontendErrLog = Join-Path $tempDir "smoke-frontend.$runId.err.log"

  $backendCmd = 'set APP_PORT=' + $backendPort + '&& cd /d "' + $backendDir + '" && "' + $pythonExe + '" -m app.main'
  $frontendCmd = 'set VITE_API_BASE_URL=' + $backendBase + '&& cd /d "' + $frontendDir + '" && npm run dev -- --host 127.0.0.1 --port ' + $frontendPort

  Write-SmokeLog "starting_backend"
  $backendProcess = Start-Process -FilePath "cmd.exe" -ArgumentList "/c", $backendCmd -PassThru -WindowStyle Hidden -RedirectStandardOutput $backendOutLog -RedirectStandardError $backendErrLog

  Write-SmokeLog "starting_frontend"
  $frontendProcess = Start-Process -FilePath "cmd.exe" -ArgumentList "/c", $frontendCmd -PassThru -WindowStyle Hidden -RedirectStandardOutput $frontendOutLog -RedirectStandardError $frontendErrLog

  Wait-UntilReady -Probe { Test-BackendHealth } -Name "backend"
  Wait-UntilReady -Probe { Test-HttpOk $frontendBase } -Name "frontend"

  Write-SmokeLog "creating_sample_pdf"
  & $pythonExe -c "import fitz; doc=fitz.open(); page=doc.new_page(width=300,height=200); page.insert_text((40,80),'Smoke Test Procurement Notice'); doc.save(r'$samplePdf'); doc.close()"

  $corpBody = @{
    name = "Smoke Test Corporation"
    business_category = "IT Services"
    region = "Seoul"
    certifications_json = "[]"
    company_size_classification = "SME"
    internal_notes = "Created by smoke test"
  } | ConvertTo-Json

  $corp = Invoke-RestMethod -Uri "$backendBase/api/corporations" -Method Post -ContentType "application/json" -Body $corpBody
  Write-SmokeLog "corporation_created id=$($corp.id)"

  $projectBody = @{
    name = "Smoke Test Project"
    corporation_id = $corp.id
    status = "active"
    notes = "Created by smoke test"
  } | ConvertTo-Json

  $proj = Invoke-RestMethod -Uri "$backendBase/api/projects" -Method Post -ContentType "application/json" -Body $projectBody
  Write-SmokeLog "project_created id=$($proj.id)"

  $uploadJson = & curl.exe -s -X POST "$backendBase/api/documents" -F "project_id=$($proj.id)" -F "document_type=notice" -F "memo=smoke" -F "revision_note=r1" -F "file=@$samplePdf;type=application/pdf"
  if (-not $uploadJson) { throw "Document upload failed (empty response)." }
  $doc = $uploadJson | ConvertFrom-Json
  Write-SmokeLog "document_uploaded id=$($doc.id)"

  $analyze = Invoke-RestMethod -Uri "$backendBase/api/documents/$($doc.id)/analyze" -Method Post
  if ($analyze.status -ne "completed") { throw "Analyze endpoint did not return completed." }
  Write-SmokeLog "analysis_completed id=$($analyze.analysis_id)"

  $latest = Invoke-RestMethod -Uri "$backendBase/api/analyses/latest/by-document/$($doc.id)" -Method Get
  if (-not $latest.id) { throw "Latest analysis lookup failed." }
  Write-SmokeLog "latest_analysis_loaded id=$($latest.id)"

  Write-Output "SMOKE_OK"
  Write-Output "backend_pid=$($backendProcess.Id)"
  Write-Output "frontend_pid=$($frontendProcess.Id)"
  Write-Output "corporation_id=$($corp.id)"
  Write-Output "project_id=$($proj.id)"
  Write-Output "document_id=$($doc.id)"
  Write-Output "analysis_id=$($latest.id)"
}
finally {
  Write-SmokeLog "stopping_servers"
  Stop-SmokeServers
  Write-SmokeLog "servers_stopped"
}
