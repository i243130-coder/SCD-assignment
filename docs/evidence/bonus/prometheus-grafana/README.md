# Evidence: Prometheus + Grafana (+2)

Steps in [../README.md](../README.md#evidence-4-prometheus--grafana).

| File | What it shows |
|---|---|
| `prometheus-targets.png` | Prometheus `/targets`: one UP target per backend pod |
| `grafana-dashboard.png` | the provisioned **CivicPulse - Backend** dashboard under load |
| `grafana-hpa-scaleout.png` | *Backend pods scraped* rising as the HPA scales out |
| `prometheus-targets.txt` | active targets (from `ops/capture-bonus-evidence.ps1`) |
| `prometheus-query.txt` | live query results for pod count and request rate |
