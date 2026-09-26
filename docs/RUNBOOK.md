# Runbook

## Deployment

### Docker Compose
```bash
docker compose -f compose.prod.yaml up -d --build
```

### Kubernetes
```bash
kubectl apply -k k8s/overlays/production
```

## Rollbacks

### Declarative (Preferred)
Revert the git commit or reapply the previous SHA overlay.
```bash
git revert <commit-sha>
git push
```

### Imperative (Emergency)
```bash
kubectl rollout undo deployment/civicpulse-backend -n civicpulse
```
**When each is appropriate**: Use `kubectl rollout undo` for immediate emergency mitigation of a broken deployment. Use declarative rollbacks to fix the state in source control.

## Reading Logs
- Docker Compose: `docker compose logs -f backend`
- Kubernetes: `kubectl logs -f deployment/civicpulse-backend -n civicpulse`

## Troubleshooting

### Triage starts failing
- Check `TRIAGE_PROVIDER` env var.
- Check Groq API status.
- Switch to rules provider: Set `TRIAGE_PROVIDER=rules` and restart.

### Monitoring
Check health and metrics:
- `/ready` endpoint
- `/metrics` endpoint

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
