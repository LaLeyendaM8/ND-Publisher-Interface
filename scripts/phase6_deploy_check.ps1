param(
  [string]$WebUrl = "https://app.negative-dialektik.com",
  [string]$ApiUrl = "https://api.negative-dialektik.com",
  [string]$Token = "",
  [string]$UserId = "00000000-0000-0000-0000-000000000001",
  [string]$UserEmail = "system@negative-dialektik.local",
  [string]$UserRole = "admin"
)

$ErrorActionPreference = "Stop"

Write-Host "1) Web login page check"
$webResp = Invoke-WebRequest -Uri "$WebUrl/login" -Method GET
Write-Host ("   status: " + $webResp.StatusCode)

Write-Host "2) API health check"
$health = Invoke-RestMethod -Uri "$ApiUrl/health" -Method GET
Write-Host ("   status: " + $health.status + ", database: " + $health.database)
if ($health.status -ne "ok") {
  throw "API health status is not ok"
}

if (-not $Token) {
  Write-Host "3) Skip protected API checks (no token provided)"
  exit 0
}

$headers = @{
  "X-Internal-Token" = $Token
  "X-User-Id" = $UserId
  "X-User-Email" = $UserEmail
  "X-User-Role" = $UserRole
}

Write-Host "3) Protected projects list check"
$projects = Invoke-RestMethod -Uri "$ApiUrl/projects" -Method GET -Headers $headers
Write-Host ("   projects_count: " + $projects.projects.Count)

Write-Host "Deployment check finished."
