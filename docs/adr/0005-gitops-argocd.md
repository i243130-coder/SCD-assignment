# ADR-0005: GitOps with Argo CD and a deploy branch

## Status
Accepted

## Context
CD previously pushed images and applied manifests imperatively into an ephemeral kind cluster. Nothing kept a real cluster matching Git, manual `kubectl` edits went unnoticed, and a rollback was a command, not a reviewed change. At the same time, bots must not push to `main` (branch protection, and −5 for direct pushes).

## Decision
- Argo CD reconciles the cluster from Git: `k8s/argocd/application.yaml` (the app) and `observability-application.yaml` (Prometheus/Grafana/Jaeger), with automated sync, `prune` and `selfHeal`.
- Argo CD tracks the branch `deploy/gitops`, not `main`. After `deploy-k8s` passes, CD's `promote-gitops` job merges `main` into that branch and commits the Cosign-verified digests into `k8s/overlays/gitops/kustomization.yaml`. `main` is never pushed to.
- Migrations run as an Argo CD Sync hook (`migrate-job.yaml`, wave 1), so a new image migrates the schema as part of the sync.
- `ignoreDifferences`: backend `/spec/replicas` (owned by the HPA) and the Secret's `/data` (real keys are set in-cluster, never committed).

## Consequences
Every production change is a commit on `deploy/gitops` naming its digests and source SHA. Drift is reverted automatically. Declarative rollback is `git revert` on the deploy branch; `kubectl rollout undo` remains the fast imperative fix, but Argo CD reverts it at the next sync unless Git changes too. The Secret must be created or patched out of band. `deploy/gitops` exists only after the first successful CD run.
