# Engineering Notes

1. **Three things that differ between laptop and CI runner, and the exact Dockerfile/manifest line that freezes each:**
   - **Python version**: `backend/Dockerfile` `FROM python:3.12-slim`
   - **Node version**: `frontend/Dockerfile` `FROM node:22-alpine`
   - **OS packages**: Pinned base images freeze the OS layer.

2. **CI/CD maturity ladder position:** Level 2 (Continuous Delivery) - automated build/test/deploy to staging. Next rung: Continuous Deployment (auto-deploy to production on green). Reference `ci.yml` and `cd.yml`.

3. **Build-once-deploy-many:** `frontend/nginx.conf` proxies `/api` to the backend service name. The same image works in dev, staging, prod. Without it, you'd need to rebuild with different API URLs per environment. Reference `nginx.conf`.

4. **Probabilistic service correctness:** With `TRIAGE_PROVIDER=llm`, the same input can give different output. "Correct" = output validates against `TriageResult` schema (category in enum, priority in enum, summary ≤140 chars). CI stays deterministic by using `SimulatedTriage`. Reference: `pyproject.toml` `[tool.pytest.ini_options]` and the `TRIAGE_PROVIDER=simulated` env in `ci.yml`.

5. **HPA lag:**
   Measured HPA lag: [RUN kubectl get hpa -w AND INSERT MEASUREMENT]

6. **VPA Off mode:** VPA Auto mode adjusts resource requests, which can trigger pod restarts. If HPA is scaling based on CPU utilization and VPA changes CPU requests, the utilization percentage changes, causing HPA thrashing. Recommender-only mode collects data without interfering. Reference: `k8s/base/vpa.yaml` `updateMode: Off`.

7. **internal:true network vs LLM:** `internal:true` blocks outbound internet. The backend needs to call the Groq API (internet). Resolution: backend is on the edge network (which allows outbound) AND internal network. This is a trade-off — the backend is more exposed than ideal, but it's the only service that needs both database access and internet access. Reference: `compose.yaml` networks section.

8. **The failure:** [TO BE FILLED WITH YOUR ACTUAL EXPERIENCE]
