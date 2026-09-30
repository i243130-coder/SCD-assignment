# Bonus evidence (capped at +15)

Each of the five bonus items in §4 of the brief, plus the two smaller "for the bonus" extras from §3 (base images pinned by digest, Actions pinned to commit SHAs). For each: where it is implemented, how to demonstrate it, and which evidence file goes in which folder.

| # | Bonus | Marks | Implemented in | Evidence folder |
|---|---|---|---|---|
| 1 | Zero-downtime rolling update under live load, zero failed requests | +4 | `k8s/base/*-deployment.yaml` (maxUnavailable 0, readiness, preStop drain, minReadySeconds), `load/k6-rollout.js`, `ops/zero-downtime-demo.ps1` | [`zero-downtime/`](zero-downtime/) |
| 2 | GitOps: Argo CD reconciling the cluster from the repository | +4 | `k8s/argocd/`, `k8s/overlays/gitops/`, `promote-gitops` job in `.github/workflows/cd.yml` | [`gitops/`](gitops/) |
| 3 | Deploy by image digest, with Cosign signing and verification in CI | +3 | `build-push` (sign) and `deploy-k8s` (verify, deploy by digest) jobs in `.github/workflows/cd.yml`; `release.yml` | [`digest-cosign/`](digest-cosign/) |
| 4 | Prometheus scraping `/metrics` + Grafana dashboard, screenshot committed | +2 | `k8s/observability/` (Prometheus pod discovery, Grafana provisioning, `grafana/civicpulse-dashboard.json`), scrape annotations in `k8s/base/backend-deployment.yaml` | [`prometheus-grafana/`](prometheus-grafana/) |
| 5 | OpenTelemetry tracing across frontend → backend → LLM call | +2 | `frontend/src/tracing.ts`, `backend/app/tracing.py`, `backend/app/routes/telemetry.py`, spans in `complaint_service.py` and `providers/triage/llm.py`, Jaeger in `k8s/observability/jaeger.yaml` | [`tracing/`](tracing/) |
| — | Base images pinned by digest (§3.1) | — | `FROM …@sha256:` in `backend/Dockerfile`, `frontend/Dockerfile` | — |
| — | Actions pinned to a commit SHA (§3.3) | — | every `uses:` in `.github/workflows/*.yml` (the tag is in the trailing comment) | — |

Two scripts produce the text evidence; screenshots are taken by hand. All commands run from the repo root in PowerShell.

- `ops/zero-downtime-demo.ps1` runs the rollout under load and saves the k6 result.
- `ops/capture-bonus-evidence.ps1` saves Argo CD status, running image digests, Prometheus targets and Jaeger traces.

---

## Order of work

The GitOps and digest items depend on CD having run once with this code, because that run creates the `deploy/gitops` branch that Argo CD watches. So:

1. **Merge this work into `main` through a PR.** CI must be green. The merge triggers CD, which builds, **signs**, **verifies**, deploys by **digest**, then **promotes** those digests to `deploy/gitops`.
2. **Phase A, on your current k3d cluster (dev overlay):** Prometheus/Grafana, tracing, zero-downtime.
3. **Phase B, GitOps:** remove the dev deployment, install Argo CD, and let it deploy the app from `deploy/gitops`.

---

## Evidence 3: Digest + Cosign (from the CD run)

After step 1, open **Actions → CD → the run for your merge commit**.

1. Screenshot the run graph showing all four jobs green: `test → build-push → deploy-k8s → promote-gitops`. Save it as `digest-cosign/cd-run.png`.
2. Open **build-push**, then:
   - Expand **Sign images by digest (keyless Cosign)**. It shows `tlog entry created` for both images. Screenshot it as `digest-cosign/cosign-sign.png`.
   - Scroll to the run **Summary**. The *Images built and signed* table lists both `sha256:` digests. Screenshot it as `digest-cosign/digests-summary.png`.
3. Open **deploy-k8s**, then:
   - Expand **Verify image signatures**. It shows `verified: ghcr.io/…@sha256:…` for both. Screenshot it as `digest-cosign/cosign-verify.png`.
   - Expand **Pin images by digest**. It prints the rendered `image: …@sha256:…` lines, proving the deployment uses digests, not tags. Screenshot it as `digest-cosign/deploy-by-digest.png`.
4. Optional: open each package in GHCR. A `sha256-….sig` tag next to the SHA tag is the stored Cosign signature.

Why it matters: a tag can be re-pointed, a digest cannot. Signing binds the digest to *this repository's CD workflow on `main`*. `cosign verify` checks exactly that identity (`--certificate-identity https://github.com/<owner>/SCD-assignment/.github/workflows/cd.yml@refs/heads/main`), so an image pushed any other way fails verification and is never deployed.

---

## Phase A: dev cluster (k3d)

The backend has new dependencies (OpenTelemetry) and the frontend has new code, so rebuild the local images first:

```powershell
docker build -t civicpulse-backend:dev backend/
docker build -t civicpulse-frontend:dev frontend/
k3d image import civicpulse-backend:dev civicpulse-frontend:dev -c civicpulse

kubectl apply -k k8s/observability            # Prometheus, Grafana, Jaeger
kubectl apply -k k8s/overlays/dev             # adds OTEL endpoint + Traefik ingress class
kubectl rollout restart deploy/backend deploy/frontend -n civicpulse
kubectl get pods -n civicpulse -w             # wait for 1/1 Running, then Ctrl+C
kubectl get pods -n observability             # prometheus, grafana, jaeger Running
```

### Evidence 4: Prometheus + Grafana

```powershell
kubectl port-forward -n observability svc/grafana 3000:3000      # terminal 2
kubectl port-forward -n observability svc/prometheus 9090:9090   # terminal 3
k6 run -e BASE_URL=http://localhost:8080 -e HOST_HEADER=civicpulse.local load/k6-rollout.js   # traffic for the graphs
```

1. Open http://localhost:9090/targets. The `civicpulse-backend` job lists **one target per backend pod**, all **UP**. Screenshot it as `prometheus-grafana/prometheus-targets.png`.
2. Open http://localhost:3000. The home dashboard is **CivicPulse - Backend** (anonymous read-only, no login). After a minute of load, screenshot the whole dashboard as `prometheus-grafana/grafana-dashboard.png`.
3. Bonus shot: run the HPA load test (`load/k6-script.js`) and watch **Backend pods scraped** and **Requests / s per pod** climb as the HPA adds replicas. Save it as `prometheus-grafana/grafana-hpa-scaleout.png`.

### Evidence 5: OpenTelemetry, frontend → backend → LLM

The trace only reaches an LLM span when the backend really calls Groq, which needs a Groq API key. **Never put the key in a file in this repo.** Put it straight into the cluster Secret:

```powershell
$env:GROQ_API_KEY = "<paste your key from console.groq.com>"
kubectl create secret generic civicpulse-secret -n civicpulse `
  --from-literal=POSTGRES_PASSWORD=changeme `
  --from-literal=GROQ_API_KEY=$env:GROQ_API_KEY `
  --dry-run=client -o yaml | kubectl apply -f -
kubectl set env deployment/backend -n civicpulse TRIAGE_PROVIDER=llm
kubectl rollout status deployment/backend -n civicpulse

kubectl port-forward -n civicpulse svc/frontend-service 3001:80      # the UI, terminal 2
kubectl port-forward -n observability svc/jaeger 16686:16686         # Jaeger UI, terminal 3
```

1. Open http://localhost:3001 and submit a complaint with **new wording each time**. Identical text is served from the Redis triage cache, so no LLM call happens.
2. Open http://localhost:16686, select service **civicpulse-frontend**, and click **Find Traces**. Open the `POST /api/complaints` trace. It should show one trace across two services:
   ```
   civicpulse-frontend   POST /api/complaints                (browser, CLIENT)
   └ civicpulse-backend  POST /api/complaints                (FastAPI, SERVER)
     └ triage                                                (triage.provider=llm:groq)
       └ llm.chat_completion                                 (gen_ai.request.model, token usage)
         └ POST                                              (httpx → api.groq.com)
   ```
   Screenshot the expanded trace as `tracing/jaeger-trace.png`, and the `llm.chat_completion` span's tags as `tracing/llm-span-attributes.png`.
3. Fallback trace (also good for the video): run `kubectl set env deployment/backend -n civicpulse GROQ_API_KEY=invalid`, submit a new complaint, and the `triage` span shows `triage.fallback=true` with the exception event. Screenshot it as `tracing/jaeger-fallback.png`. Restore the key afterwards by re-running the Secret command and `kubectl set env deployment/backend -n civicpulse GROQ_API_KEY-`.

No key yet? Everything else still traces (frontend → backend → triage). Only the two LLM spans are missing, and the brief asks for them, so get a free key before recording.

### Evidence 1: Zero-downtime rolling update

The k3d load balancer on :8080 forwards to Traefik, which routes by Ingress through the Services. That's the path real traffic takes during a rollout.

```powershell
powershell -ExecutionPolicy Bypass -File ops/zero-downtime-demo.ps1
```

The script:

- starts `load/k6-rollout.js`: a constant 20 iterations/s (60 req/s) for 2 minutes, with a **threshold `http_req_failed rate==0`** so k6 itself fails if any request fails;
- after 20 s, runs `kubectl rollout restart` on backend **and** frontend, and waits for both rollouts;
- writes `zero-downtime/rollout.txt`, `zero-downtime/k6-output.txt` and `zero-downtime/k6-summary.json`.

Screenshot the final k6 summary showing `http_req_failed ... 0.00%` and the green `ZERO DOWNTIME` line as `zero-downtime/k6-zero-failures.png`. Record it for the video too.

How it gets to zero: `maxUnavailable: 0` + `maxSurge: 1` means a new pod must pass `/ready` (and stay ready for `minReadySeconds: 5`) before an old one is removed. The `preStop` sleep keeps the old pod serving for 5 s while Traefik and kube-proxy drop it from their endpoints, so in-flight requests finish. The PodDisruptionBudget keeps at least one backend pod available.

---

## Phase B: GitOps with Argo CD

### Evidence 2: GitOps

Argo CD will own namespace `civicpulse`, so remove the kubectl-managed dev copy first. The observability stack can stay; Argo CD adopts it.

The base includes a VerticalPodAutoscaler, so the VPA CRD must exist in the cluster, or the sync fails on that one object. `kubectl get crd verticalpodautoscalers.autoscaling.k8s.io` should find it. If not, run `kubectl apply -f https://raw.githubusercontent.com/kubernetes/autoscaler/vertical-pod-autoscaler-1.8.0/vertical-pod-autoscaler/deploy/vpa-v1-crd-gen.yaml`.

```powershell
kubectl delete namespace civicpulse

kubectl create namespace argocd
kubectl apply -n argocd --server-side --force-conflicts -f https://raw.githubusercontent.com/argoproj/argo-cd/v3.5.3/manifests/install.yaml
kubectl wait --for=condition=available deployment --all -n argocd --timeout=300s

kubectl apply -k k8s/argocd                      # the two Applications
kubectl get applications -n argocd -w            # wait for Synced / Healthy
```

Argo CD UI:

```powershell
$pw = kubectl -n argocd get secret argocd-initial-admin-secret -o jsonpath="{.data.password}"
[Text.Encoding]::UTF8.GetString([Convert]::FromBase64String($pw))    # password for user "admin"
kubectl port-forward -n argocd svc/argocd-server 8443:443            # then https://localhost:8443
```

1. **Synced from Git:** screenshot the `civicpulse` app tree, Synced + Healthy, source `deploy/gitops`, with the `backend-migrate` hook completed. Save it as `gitops/argocd-app-synced.png`.
2. **Deployed by digest:** in the app, click a backend pod. Its image is `ghcr.io/…/civicpulse-backend@sha256:…`. Save it as `gitops/argocd-pod-digest.png`.
3. **Drift is reverted (self-heal):** run `kubectl scale deployment/frontend -n civicpulse --replicas=5`, and within seconds Argo CD scales it back to what Git says. Screenshot the app's events or history as `gitops/argocd-selfheal.png`.
4. **Declarative rollback:** revert the last promotion on the deploy branch; Argo CD syncs the previous digest.
   ```powershell
   git fetch origin
   git switch -c rollback-demo origin/deploy/gitops
   git log --oneline -3 -- k8s/overlays/gitops/kustomization.yaml   # the deploy commits
   git revert --no-edit HEAD
   git push origin HEAD:deploy/gitops
   git switch -          # back to your branch; `git branch -D rollback-demo` when done
   ```
   Screenshot the Argo CD history showing the new sync to the older revision as `gitops/argocd-rollback.png`.

Then run `ops/capture-bonus-evidence.ps1`. It writes `gitops/*.txt`, `digest-cosign/*.txt`, `prometheus-grafana/*.txt` and `tracing/*.txt` from the live cluster.

The GitOps flow: CD never runs `kubectl` against the real cluster, and nobody pushes to `main`. After `deploy-k8s` passes, `promote-gitops` commits the verified digests to `k8s/overlays/gitops/kustomization.yaml` on `deploy/gitops`. Argo CD watches that branch and reconciles the cluster, pruning what Git removed and undoing manual drift. The HPA-managed replica count and the Secret's data (the Groq key) are listed under `ignoreDifferences`, so Git does not fight them.

---

## Checklist

- [ ] PR merged, CD run green with all 4 jobs (`digest-cosign/cd-run.png`)
- [ ] Cosign sign + verify screenshots (`digest-cosign/`)
- [ ] Prometheus targets + Grafana dashboard screenshots (`prometheus-grafana/`)
- [ ] Jaeger trace frontend → backend → LLM (`tracing/jaeger-trace.png`)
- [ ] `ops/zero-downtime-demo.ps1` output with `http_req_failed 0.00%` (`zero-downtime/`)
- [ ] Argo CD synced, self-heal and rollback screenshots (`gitops/`)
- [ ] `ops/capture-bonus-evidence.ps1` run, text files committed
- [ ] Each item shown in the demo video
