# Runbook

## Deployment

### Docker Compose
```bash
docker compose -f compose.prod.yaml up -d --build
```

### Kubernetes (local dev, k3d)
```bash
kubectl apply -k k8s/overlays/dev
kubectl apply -k k8s/observability   # Prometheus, Grafana, Jaeger
```

### Kubernetes (GitOps, Argo CD)
Production-style deploys are not applied by hand. Merging to `main` runs CD, which signs the images, verifies the signatures, and promotes their digests to the `deploy/gitops` branch. Argo CD syncs `k8s/overlays/gitops` from that branch. First-time setup (Argo CD install + `kubectl apply -k k8s/argocd`) is in [docs/evidence/bonus/README.md](evidence/bonus/README.md#evidence-2-gitops).

"What is production running?"
```bash
kubectl get deploy -n civicpulse -o jsonpath='{range .items[*]}{.metadata.name}{"\t"}{.spec.template.spec.containers[0].image}{"\n"}{end}'
git log origin/deploy/gitops -1 -- k8s/overlays/gitops/kustomization.yaml
```

## Rollbacks

### Declarative (Preferred)
Revert the promotion commit on the deploy branch; Argo CD syncs the previous digests.
```bash
git fetch origin
git switch -c rollback origin/deploy/gitops
git revert --no-edit <deploy-commit>      # see: git log -- k8s/overlays/gitops/kustomization.yaml
git push origin HEAD:deploy/gitops
```

### Imperative (Emergency)
```bash
kubectl rollout undo deployment/backend -n civicpulse
```
**When each is appropriate**: Use `kubectl rollout undo` at 3 a.m. for immediate mitigation. Under Argo CD self-heal it only holds until the next sync, so follow it with the declarative revert to fix the state in source control.

## Reading Logs
- Docker Compose: `docker compose logs -f backend`
- Kubernetes: `kubectl logs -f deployment/backend -n civicpulse`

## Troubleshooting

### Triage starts failing
- Check `TRIAGE_PROVIDER` env var.
- Check Groq API status.
- Switch to rules provider: Set `TRIAGE_PROVIDER=rules` and restart.

### Monitoring
Check health and metrics:
- `/ready` endpoint
- `/metrics` endpoint
- Grafana: `kubectl port-forward -n observability svc/grafana 3000:3000`, then http://localhost:3000 ("CivicPulse - Backend": request rate, p95 latency, triage fallbacks, pods scraped)
- Traces: `kubectl port-forward -n observability svc/jaeger 16686:16686`, then http://localhost:16686 (service `civicpulse-frontend` or `civicpulse-backend`). A failed LLM call shows as `triage.fallback=true` on the `triage` span.

## Database Operations

### Run Migrations
```bash
docker compose exec backend alembic upgrade head
```

### Seed Data
```bash
docker compose exec backend python -m scripts.seed
```

## Common Issues and Solutions
- **Database Connection Error**: Ensure PostgreSQL container is running and healthy. Check credentials in `.env`.
- **Redis Connection Error**: Ensure Redis container is running.
- **LLM Rate Limits**: Check Groq dashboard, consider fallback or caching strategies.
