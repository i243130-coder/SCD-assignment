<#
.SYNOPSIS
  Bonus evidence: rolling update under live load with zero failed requests.

.DESCRIPTION
  Starts load/k6-rollout.js against the Ingress, restarts the backend and
  frontend Deployments mid-test, waits for both rollouts, and saves:
    docs/evidence/bonus/zero-downtime/rollout.txt      (kubectl output)
    docs/evidence/bonus/zero-downtime/k6-output.txt    (full k6 run)
    docs/evidence/bonus/zero-downtime/k6-summary.json  (machine-readable)
  k6 exits non-zero if http_req_failed is above 0, and this script reports it.

.EXAMPLE
  # from the repo root, with the app reachable on http://localhost:8080
  powershell -ExecutionPolicy Bypass -File ops/zero-downtime-demo.ps1
#>
param(
  [string]$Namespace = "civicpulse",
  [string[]]$Deployments = @("backend", "frontend"),
  [string]$BaseUrl = "http://localhost:8080",
  [string]$HostHeader = "civicpulse.local",
  [string]$Duration = "2m",
  [string]$OutDir = "docs/evidence/bonus/zero-downtime"
)

# Continue, not Stop: in Windows PowerShell 5.1, a native command writing to
# stderr under "2>&1" would otherwise abort the script.
$ErrorActionPreference = "Continue"
New-Item -ItemType Directory -Force -Path $OutDir | Out-Null
$repo = (Get-Location).Path
$log = Join-Path $OutDir "rollout.txt"

function Log([object[]]$Lines) {
  $Lines | Out-File -FilePath $log -Append -Encoding utf8
  $Lines | ForEach-Object { Write-Host $_ }
}

"# Zero-downtime rollout under load - $(Get-Date -Format o)" | Out-File -FilePath $log -Encoding utf8
Log "Images before:"
Log (kubectl get deploy -n $Namespace -o "jsonpath={range .items[*]}{.metadata.name}{'\t'}{.spec.template.spec.containers[0].image}{'\n'}{end}" 2>&1)

Write-Host "Starting k6 ($Duration) against $BaseUrl ..."
$k6 = Start-Job -ScriptBlock {
  param($repo, $base, $hostHeader, $duration, $out)
  Set-Location $repo
  k6 run -e BASE_URL=$base -e HOST_HEADER=$hostHeader -e DURATION=$duration `
    --summary-export (Join-Path $out "k6-summary.json") load/k6-rollout.js 2>&1
  "K6_EXIT_CODE=$LASTEXITCODE"
} -ArgumentList $repo, $BaseUrl, $HostHeader, $Duration, $OutDir

# Let traffic reach steady state before touching the pods.
Start-Sleep -Seconds 20

foreach ($d in $Deployments) {
  Log "`n> kubectl rollout restart deployment/$d -n $Namespace   ($(Get-Date -Format T))"
  Log (kubectl rollout restart deployment/$d -n $Namespace 2>&1)
}
foreach ($d in $Deployments) {
  Log "`n> kubectl rollout status deployment/$d -n $Namespace"
  Log (kubectl rollout status deployment/$d -n $Namespace --timeout=180s 2>&1)
}
Log "`n> kubectl get pods -n $Namespace -o wide   ($(Get-Date -Format T))"
Log (kubectl get pods -n $Namespace -o wide 2>&1)
Log "`n> kubectl rollout history deployment/backend -n $Namespace"
Log (kubectl rollout history deployment/backend -n $Namespace 2>&1)

Write-Host "`nWaiting for k6 to finish ..."
$result = Receive-Job -Job $k6 -Wait -AutoRemoveJob
$result | Out-File -FilePath (Join-Path $OutDir "k6-output.txt") -Encoding utf8
$result | Select-Object -Last 35 | ForEach-Object { Write-Host $_ }

$failedLine = $result | Where-Object { $_ -match "http_req_failed" } | Select-Object -First 1
$exit = ($result | Where-Object { $_ -match "^K6_EXIT_CODE=" } | Select-Object -Last 1) -replace "K6_EXIT_CODE=", ""
Write-Host ""
if ($exit -eq "0") {
  Write-Host "ZERO DOWNTIME: every request succeeded during the rollout." -ForegroundColor Green
} else {
  Write-Host "Requests failed during the rollout (k6 exit $exit). See $OutDir/k6-output.txt" -ForegroundColor Red
}
if ($failedLine) { Write-Host $failedLine }
Write-Host "Evidence saved in $OutDir"
