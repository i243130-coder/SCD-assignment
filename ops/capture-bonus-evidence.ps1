<#
.SYNOPSIS
  Saves text evidence for the GitOps, digest+Cosign, Prometheus/Grafana and
  OpenTelemetry bonus items into docs/evidence/bonus/<item>/.

.DESCRIPTION
  Run from the repo root once Argo CD, the app and k8s/observability are up.
  Screenshots are still taken by hand (see docs/evidence/bonus/README.md);
  this script produces the matching command output so every screenshot has a
  text record next to it.

.EXAMPLE
  powershell -ExecutionPolicy Bypass -File ops/capture-bonus-evidence.ps1
#>
param(
  [string]$Namespace = "civicpulse",
  [string]$Owner = "i243130-coder",
  [string]$OutRoot = "docs/evidence/bonus"
)

$ErrorActionPreference = "Continue"

function Save([string]$Item, [string]$Name, [scriptblock]$Block) {
  $dir = Join-Path $OutRoot $Item
  New-Item -ItemType Directory -Force -Path $dir | Out-Null
  $file = Join-Path $dir $Name
  $header = "# $Name - captured $(Get-Date -Format o)"
  $body = & $Block 2>&1 | Out-String
  ($header, $body) | Out-File -FilePath $file -Encoding utf8
  Write-Host "saved $file"
}

function With-PortForward([string]$Ns, [string]$Svc, [int]$Port, [scriptblock]$Block) {
  $pf = Start-Job -ScriptBlock { param($ns, $svc, $port) kubectl port-forward -n $ns "svc/$svc" "${port}:${port}" } -ArgumentList $Ns, $Svc, $Port
  Start-Sleep -Seconds 4
  try { & $Block } finally { Stop-Job $pf; Remove-Job $pf -Force }
}

# -- GitOps (Argo CD) -----------------------------------------
Save "gitops" "argocd-applications.txt" {
  kubectl get applications -n argocd -o wide
  ""
  "Sync revision / status per app:"
  kubectl get applications -n argocd -o "jsonpath={range .items[*]}{.metadata.name}{'\t'}{.status.sync.status}{'\t'}{.status.health.status}{'\t'}{.status.sync.revision}{'\n'}{end}"
}
Save "gitops" "deploy-branch-log.txt" {
  git fetch origin deploy/gitops --quiet
  git log origin/deploy/gitops -5 --format="%h %ad %s%n%b" --date=iso -- k8s/overlays/gitops/kustomization.yaml
}

# -- Deploy by digest + Cosign --------------------------------
Save "digest-cosign" "running-images.txt" {
  "Images running in namespace $Namespace (note @sha256 - pinned by digest, not tag):"
  kubectl get pods -n $Namespace -o "jsonpath={range .items[*]}{.metadata.name}{'\t'}{.spec.containers[0].image}{'\n'}{end}"
}
Save "digest-cosign" "cosign-verify.txt" {
  if (Get-Command cosign -ErrorAction SilentlyContinue) {
    $images = kubectl get deploy -n $Namespace -o "jsonpath={range .items[*]}{.spec.template.spec.containers[0].image}{'\n'}{end}" |
      Where-Object { $_ -match "@sha256:" } | Sort-Object -Unique
    foreach ($img in $images) {
      "> cosign verify $img"
      cosign verify $img `
        --certificate-identity "https://github.com/$Owner/SCD-assignment/.github/workflows/cd.yml@refs/heads/main" `
        --certificate-oidc-issuer https://token.actions.githubusercontent.com
      ""
    }
  } else {
    "cosign is not installed locally - the verification evidence is the"
    "'Verify image signatures' step of the CD run (see README in this folder)."
  }
}

# -- Prometheus / Grafana -------------------------------------
With-PortForward "observability" "prometheus" 9090 {
  Save "prometheus-grafana" "prometheus-targets.txt" {
    $t = Invoke-RestMethod "http://localhost:9090/api/v1/targets?state=active"
    $t.data.activeTargets | Select-Object @{n = "job"; e = { $_.labels.job } }, @{n = "pod"; e = { $_.labels.pod } }, scrapeUrl, health, lastScrape |
      Format-Table -AutoSize | Out-String -Width 250
  }
  Save "prometheus-grafana" "prometheus-query.txt" {
    foreach ($q in @('count(up{job="civicpulse-backend"} == 1)', 'sum by (status) (rate(http_requests_total{job="civicpulse-backend"}[5m]))')) {
      "> $q"
      (Invoke-RestMethod "http://localhost:9090/api/v1/query?query=$([uri]::EscapeDataString($q))").data.result | ConvertTo-Json -Depth 6
      ""
    }
  }
}

# -- OpenTelemetry / Jaeger -----------------------------------
With-PortForward "observability" "jaeger" 16686 {
  Save "tracing" "jaeger-services.txt" {
    (Invoke-RestMethod "http://localhost:16686/api/services").data
  }
  Save "tracing" "jaeger-recent-traces.txt" {
    $traces = (Invoke-RestMethod "http://localhost:16686/api/traces?service=civicpulse-frontend&limit=20&lookback=1h").data
    foreach ($tr in $traces) {
      $services = $tr.processes.PSObject.Properties.Value.serviceName | Sort-Object -Unique
      $names = $tr.spans | Sort-Object startTime | ForEach-Object { $_.operationName }
      "trace $($tr.traceID)  services=[$($services -join ', ')]  spans=$($tr.spans.Count)"
      "   " + ($names -join "  ->  ")
    }
    if (-not $traces) { "No frontend traces yet - submit a complaint in the UI first." }
  }
}

Write-Host "`nDone. Add the screenshots listed in $OutRoot/README.md next to these files."
