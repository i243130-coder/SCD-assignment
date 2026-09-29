# Engineering Notes

This document provides rigorous, file-and-line answers to the eight mandatory engineering reflection questions specified in §5.2 of the assignment brief.

---

### 1. Three things that differ between your laptop and a CI runner, and the exact line in a Dockerfile or manifest that freezes each

1. **Python Runtime and Minor Version / ABI**:
   - *Difference:* Host developer machines run varying Python versions (e.g., Python 3.12, 3.13, 3.14 on macOS/Windows/Linux) with differing C runtime libraries.
   - *Exact Freezing Line:* [`backend/Dockerfile` line 2 and line 7](file:///c:/Users/Abdul%20Moez/Documents/GitHub/SCD-assignment/backend/Dockerfile#L2-L7):
     ```dockerfile
     FROM python:3.12-slim AS builder
     ...
     FROM python:3.12-slim
     ```

2. **Node.js Toolchain and Package Manager Versions**:
   - *Difference:* Developer machines frequently have varying versions of Node.js (v18, v20, v22) or npm/pnpm/yarn, resulting in divergent package trees and lockfile drift.
   - *Exact Freezing Line:* [`frontend/Dockerfile` line 2 and line 9](file:///c:/Users/Abdul%20Moez/Documents/GitHub/SCD-assignment/frontend/Dockerfile#L2-L9):
     ```dockerfile
     FROM node:22-alpine AS builder
     ...
     FROM nginx:1.27-alpine
     ```

3. **Database Schema, Storage, and User Environment**:
   - *Difference:* Local environments might use ephemeral in-memory sqlite or variable host databases, whereas production requires a fixed, reproducible PostgreSQL version with strict volume persistence.
   - *Exact Freezing Line:* [`compose.yaml` line 60](file:///c:/Users/Abdul%20Moez/Documents/GitHub/SCD-assignment/compose.yaml#L60) and [`k8s/base/postgres.yaml` line 18](file:///c:/Users/Abdul%20Moez/Documents/GitHub/SCD-assignment/k8s/base/postgres.yaml#L18):
     ```yaml
     image: postgres:16-alpine
     ```

---

### 2. Where your pipeline sits on the CI/CD maturity ladder (Lecture 03, slide 32). Justify the rung; name the next rung and what it buys.

- **Current Rung:** **Level 2 — Continuous Delivery (Automated Build & Test with Staging Deployment)**.
- **Justification:** Every pull request to `main` triggers automated linting, typechecking, unit/integration testing, container builds, and security scans ([`.github/workflows/ci.yml`](file:///c:/Users/Abdul%20Moez/Documents/GitHub/SCD-assignment/.github/workflows/ci.yml)). Merges to `main` build immutable SHA-tagged artifacts pushed to GHCR and automatically deploy to an ephemeral Kubernetes cluster via kind with ingress smoke tests ([`.github/workflows/cd.yml`](file:///c:/Users/Abdul%20Moez/Documents/GitHub/SCD-assignment/.github/workflows/cd.yml)).
- **Next Rung:** **Level 3 — Continuous Deployment (GitOps with Automated Canary/Progressive Rollouts)**.
- **What it Buys:** Continuous Deployment directly to live customer-facing production without human gatekeeping, accompanied by automated canary analysis (e.g. Argo Rollouts or Flagger). It buys zero-touch release velocity, automatic rollback upon elevated HTTP error rates, and elimination of manual deployment risk.

---

### 3. The exact line guaranteeing build-once-deploy-many, and what breaks without it

- **Exact Freezing Line:** [`frontend/nginx.conf` lines 9–14](file:///c:/Users/Abdul%20Moez/Documents/GitHub/SCD-assignment/frontend/nginx.conf#L9-L14):
  ```nginx
  location /api/ {
      proxy_pass http://backend;
      proxy_set_header Host $host;
      proxy_set_header X-Real-IP $remote_addr;
      proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
  }
  ```
- **What Breaks Without It:** 
  A standard Vite build statically bakes `import.meta.env` values into bundled JavaScript artifacts at build time. If the backend URL (e.g. `http://localhost:8000` vs `http://api.civicpulse.org`) were hardcoded or baked in, the frontend Docker image would be strictly bound to a single environment. Moving from dev to staging to prod would require rebuilding the image, violating the 12-factor principle and destroying build-once-deploy-many. By proxying `/api` through Nginx to the internal service name `backend`, the frontend makes relative calls (`/api/...`), allowing the identical container image to execute seamlessly across local Docker, Kubernetes, and cloud environments without rebuilding.

---

### 4. With a live LLM provider your service is probabilistic. What does "correct" mean for that component, and how did you keep CI deterministic? (Lecture 01, slide 34)

- **What "Correct" Means:** 
  An LLM output cannot be evaluated with exact string equality because LLM responses are inherently non-deterministic and probabilistic. Instead, "correctness" is defined by **structural contract adherence and semantic invariants**:
  1. The response parses into valid JSON conforming to the Pydantic [`TriageResult` schema](file:///c:/Users/Abdul%20Moez/Documents/GitHub/SCD-assignment/backend/app/providers/triage/base.py#L10-L16).
  2. The `category` strictly belongs to the defined `Category` enum.
  3. The `priority` strictly belongs to the defined `Priority` enum.
  4. The `summary` is non-empty and does not exceed 140 characters.
  5. The `confidence` is a float bounded within `[0.0, 1.0]`.
- **How CI Stays Deterministic:** 
  In automated CI and test environments, live external LLM API calls are eliminated. Instead, `TRIAGE_PROVIDER=simulated` is pinned in the test matrix and CI workflow ([`.github/workflows/cd.yml` line 11](file:///c:/Users/Abdul%20Moez/Documents/GitHub/SCD-assignment/.github/workflows/cd.yml#L11) and [`backend/tests/conftest.py` line 85](file:///c:/Users/Abdul%20Moez/Documents/GitHub/SCD-assignment/backend/tests/conftest.py#L85)). [`SimulatedTriage`](file:///c:/Users/Abdul%20Moez/Documents/GitHub/SCD-assignment/backend/app/providers/triage/simulated.py) uses a seeded MD5/SHA hash of the input text to deterministically return the same category, priority, and summary on every test run with zero network dependencies or flakiness.

---

### 5. Your HPA lag: how many seconds between offered load rising and replicas rising? Where did the time go, and what would reduce it?

- **Observed / Measured HPA Lag:** ~30 to 45 seconds between offered traffic spike and the second replica becoming `Ready`.
- **Where the Time Went:**
  1. **Metrics-Server Scraping Interval (15s):** Kubernetes `metrics-server` scrapes kubelet cadvisor metrics periodically (default 15–30s).
  2. **HPA Controller Evaluation Loop (15s):** The horizontal pod autoscaler controller loops every `--horizontal-pod-autoscaler-sync-period` (default 15s) to re-evaluate CPU metrics against target utilization (`60%`).
  3. **Container Creation and Readiness Probes (~5–10s):** Time taken to pull/start the container, run python startup, and satisfy `periodSeconds: 2` of the `readinessProbe` ([`k8s/base/backend.yaml`](file:///c:/Users/Abdul%20Moez/Documents/GitHub/SCD-assignment/k8s/base/backend.yaml)).
- **What Would Reduce It:**
  1. Setting `metrics-server` metric resolution interval to `--metric-resolution=5s`.
  2. Configuring Kube-controller-manager `--horizontal-pod-autoscaler-sync-period=5s`.
  3. Scaling on Prometheus custom metrics (e.g. HTTP request rate per second from `/metrics`) rather than CPU utilization, because request rate spikes instantaneously before CPU saturates.

---

### 6. Why VPA is in Off mode. Describe the failure mode of running it in Auto alongside your HPA.

- **Exact Manifest Configuration:** [`k8s/base/vpa.yaml` line 13](file:///c:/Users/Abdul%20Moez/Documents/GitHub/SCD-assignment/k8s/base/vpa.yaml#L13): `updateMode: "Off"`.
- **Why VPA is in Off Mode & The Cyclic Failure Mode:**
  Both HPA and VPA are autonomous control loops attempting to react to resource utilization:
  $$\text{Utilization} = \frac{\text{Actual CPU Usage}}{\text{CPU Request}}$$
  1. When traffic surges, actual CPU usage rises.
  2. **HPA reaction:** Sees utilization > 60%, and schedules additional pods to scale horizontally.
  3. **VPA (in Auto mode) reaction:** Observes elevated CPU usage and mutates the pod specification to increase the pod's `resources.requests.cpu`.
  4. Once `requests.cpu` is increased, the denominator grows, causing the computed CPU utilization percentage to abruptly plunge below the target threshold.
  5. **HPA counter-reaction:** Sees low utilization and initiates horizontal scale-in (evicting pods).
  6. With fewer pods remaining, per-pod load increases again, inducing VPA to increase requests even further.
  7. This cyclic competition creates control loop oscillation (thrashing), unnecessary pod restarts/evictions, and cluster instability. Setting VPA to `Off` (recommender mode) allows human operators to observe realistic resource requirements without triggering conflicting automated mutations.

---

### 7. Your internal: true network blocks outbound traffic. Where does that leave the service that calls a hosted LLM, and how did you resolve it?

- **Architectural Consequence:**
  In [`compose.yaml` lines 105–107](file:///c:/Users/Abdul%20Moez/Documents/GitHub/SCD-assignment/compose.yaml#L105-L107), `internal: true` creates an isolated bridge network that prevents any outbound packets to the external internet:
  ```yaml
  internal:
    driver: bridge
    internal: true
  ```
  Consequently, containers attached solely to `internal` (PostgreSQL and Redis) cannot contact external hosts, which guarantees that database contents cannot be exfiltrated. However, an external LLM provider (`LLMTriage` calling `https://api.groq.com`) requires internet connectivity.
- **How It Was Resolved:**
  The `backend` container serves as a dual-homed secure bridge between networks ([`compose.yaml` lines 30–32](file:///c:/Users/Abdul%20Moez/Documents/GitHub/SCD-assignment/compose.yaml#L30-L32)):
  - Backend is joined to **both** `edge` (which has external internet egress) and `internal` (which can reach PostgreSQL and Redis).
  - The `frontend` is joined **only** to `edge` and has no entry to `internal`, making direct access to the database strictly impossible (`docker compose exec frontend ping postgres` fails with `bad address 'postgres'`).
  - This preserves network segmentation for the data tier while enabling outbound HTTPS requests from the API backend to Groq.

---

### 8. The failure: Something cost you more than an hour. Symptoms, what you wrongly believed first, and the exact command or log line that finally told you the truth.

- **Symptoms:** 
  The frontend complaint intake form consistently failed on submit with a generic API failure, and browser inspection showed `Failed to execute 'text' on 'Response': body stream already read`. The backend returned HTTP 500 `Internal Server Error` for `POST /api/complaints`.
- **What Was Wrongly Believed First:** 
  It was initially assumed that the Groq LLM API quota was exhausted or returning unexpected JSON formats that corrupted the triage pipeline, or that client-side fetch handling had misconfigured headers.
- **The Exact Command and Log Line that Revealed the Truth:**
  - **Inspection Command:**
    ```bash
    docker logs --tail 100 scd-assignment-backend-1
    ```
  - **Exact Traceback and Error Line:**
    ```text
    sqlalchemy.exc.ProgrammingError: (sqlalchemy.dialects.postgresql.asyncpg.ProgrammingError) 
    <class 'asyncpg.exceptions.UndefinedTableError'>: relation "complaints" does not exist
    [SQL: INSERT INTO complaints (id, text, location, ...) VALUES ($1::UUID, ...)]
    ```
  - **Root Cause & Resolution:** 
    While Docker Compose started the PostgreSQL container, the schema migration had never been executed against the database volume, meaning the `complaints` table was absent. Additionally, Alembic's `alembic.ini` and `env.py` were initially relying on hardcoded connection strings rather than reading `${DATABASE_URL}`. Updating `alembic/env.py` to read `os.getenv("DATABASE_URL")` and running `docker compose exec backend alembic upgrade head` created the schema, indexes, and constraints, immediately resolving the 500 error.

