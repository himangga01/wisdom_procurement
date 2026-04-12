$ErrorActionPreference = "Stop"

$root = Split-Path -Parent $PSScriptRoot
$backendDir = Join-Path $root "backend"
$tempDir = Join-Path $root "temp"
$samplePdf = Join-Path $tempDir "smoke-sample.pdf"
$backendBase = "http://127.0.0.1:18111"
$manageScript = Join-Path $PSScriptRoot "manage-servers.ps1"

New-Item -ItemType Directory -Force $tempDir | Out-Null

try {
  powershell -ExecutionPolicy Bypass -File $manageScript -Action start -BackendPort 18111 -FrontendPort 5199 | Out-Null

  & (Join-Path $backendDir ".venv\Scripts\python") -c "from pypdf import PdfWriter; w=PdfWriter(); w.add_blank_page(width=300,height=200); f=open(r'$samplePdf','wb'); w.write(f); f.close()"

  $corp = Invoke-RestMethod -Uri "$backendBase/api/corporations" -Method Post -ContentType "application/json" -Body (@{ name = "스모크법인" } | ConvertTo-Json)
  $proj = Invoke-RestMethod -Uri "$backendBase/api/projects" -Method Post -ContentType "application/json" -Body (@{ name = "스모크프로젝트"; corporation_id = $corp.id } | ConvertTo-Json)

  $uploadJson = & curl.exe -s -X POST "$backendBase/api/documents" -F "project_id=$($proj.id)" -F "document_type=notice" -F "memo=smoke" -F "revision_note=r1" -F "file=@$samplePdf;type=application/pdf"
  if (-not $uploadJson) { throw "Document upload failed (empty response)." }
  $doc = $uploadJson | ConvertFrom-Json

  $analyze = Invoke-RestMethod -Uri "$backendBase/api/documents/$($doc.id)/analyze" -Method Post
  if ($analyze.status -ne "completed") { throw "Analyze endpoint did not return completed." }

  $latest = Invoke-RestMethod -Uri "$backendBase/api/analyses/latest/by-document/$($doc.id)" -Method Get
  if (-not $latest.id) { throw "Latest analysis lookup failed." }

  $status = powershell -ExecutionPolicy Bypass -File $manageScript -Action status -BackendPort 18111 -FrontendPort 5199

  Write-Output "SMOKE_OK"
  Write-Output $status
  Write-Output "corporation_id=$($corp.id)"
  Write-Output "project_id=$($proj.id)"
  Write-Output "document_id=$($doc.id)"
  Write-Output "analysis_id=$($latest.id)"
}
finally {
  powershell -ExecutionPolicy Bypass -File $manageScript -Action stop -BackendPort 18111 -FrontendPort 5199 | Out-Null
}
