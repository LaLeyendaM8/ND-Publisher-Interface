param(
  [string]$BaseUrl = "http://localhost:8000",
  [string]$Token = "",
  [int]$PollSeconds = 2,
  [int]$MaxPolls = 15
)

$ErrorActionPreference = "Stop"

function Invoke-ApiJson {
  param(
    [string]$Method,
    [string]$Url,
    [object]$Body = $null
  )
  $headers = @{}
  if ($Token) {
    $headers["X-Internal-Token"] = $Token
  }
  if ($Body -ne $null) {
    return Invoke-RestMethod -Method $Method -Uri $Url -Headers $headers -ContentType "application/json" -Body ($Body | ConvertTo-Json -Depth 8)
  }
  return Invoke-RestMethod -Method $Method -Uri $Url -Headers $headers
}

Write-Host "1) Create project"
$project = Invoke-ApiJson -Method "POST" -Url "$BaseUrl/projects" -Body @{ name = "Smoke Test Project" }
Write-Host ("   project_id: " + $project.project_id)

$tmpFile = Join-Path $env:TEMP ("nd_smoke_" + [guid]::NewGuid().ToString("N") + ".txt")
"Texto de prueba para smoke test." | Set-Content -Path $tmpFile -Encoding UTF8

Write-Host "2) Upload file"
$uploadUrl = "$BaseUrl/projects/$($project.project_id)/files"
$curlArgs = @("-sS", "-X", "POST", $uploadUrl, "-F", "file=@$tmpFile")
if ($Token) {
  $curlArgs = @("-sS", "-X", "POST", $uploadUrl, "-H", "X-Internal-Token: $Token", "-F", "file=@$tmpFile")
}
$uploadRaw = & curl.exe @curlArgs
$upload = $uploadRaw | ConvertFrom-Json
Write-Host ("   file_id: " + $upload.file_id)

Write-Host "3) Start project job (proofcheck)"
$job = Invoke-ApiJson -Method "POST" -Url "$BaseUrl/projects/$($project.project_id)/jobs" -Body @{
  tool = "proofcheck"
  file_id = $upload.file_id
  options = @{}
}
Write-Host ("   job_id: " + $job.job_id)
Write-Host ("   initial_status: " + $job.status)

Write-Host "4) Poll status"
$status = $job.status
for ($i = 0; $i -lt $MaxPolls; $i++) {
  Start-Sleep -Seconds $PollSeconds
  $jobStatus = Invoke-ApiJson -Method "GET" -Url "$BaseUrl/projects/$($project.project_id)/jobs/$($job.job_id)"
  $status = $jobStatus.status
  Write-Host ("   poll " + ($i + 1) + ": " + $status)
  if ($status -eq "done" -or $status -eq "failed") {
    Write-Host ("   final_message: " + $jobStatus.message)
    break
  }
}

Write-Host "5) List project jobs"
$jobs = Invoke-ApiJson -Method "GET" -Url "$BaseUrl/projects/$($project.project_id)/jobs"
Write-Host ("   jobs_count: " + $jobs.jobs.Count)

if (Test-Path $tmpFile) {
  Remove-Item -LiteralPath $tmpFile -Force
}

Write-Host "Smoke test finished."
