# Evidence: zero-downtime rolling update (+4)

Produced by `ops/zero-downtime-demo.ps1` (steps in [../README.md](../README.md#evidence-1-zero-downtime-rolling-update)).

| File | What it shows |
|---|---|
| `k6-zero-failures.png` | k6 summary: `http_req_failed 0.00%` while every pod was replaced |
| `k6-output.txt` | full k6 run (threshold `http_req_failed rate==0` passed) |
| `k6-summary.json` | machine-readable k6 metrics |
| `rollout.txt` | the `kubectl rollout restart / status` output and pod list, with timestamps |
