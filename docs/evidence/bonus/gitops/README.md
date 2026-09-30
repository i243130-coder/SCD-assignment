# Evidence: GitOps with Argo CD (+4)

Steps in [../README.md](../README.md#evidence-2-gitops).

| File | What it shows |
|---|---|
| `argocd-app-synced.png` | `civicpulse` app Synced + Healthy from branch `deploy/gitops` |
| `argocd-pod-digest.png` | a pod running `image@sha256:…` put there by Argo CD |
| `argocd-selfheal.png` | a manual `kubectl scale` reverted to the Git state |
| `argocd-rollback.png` | `git revert` on `deploy/gitops` → Argo CD syncs the previous digest |
| `argocd-applications.txt` | `kubectl get applications -n argocd` (from `ops/capture-bonus-evidence.ps1`) |
| `deploy-branch-log.txt` | the promotion commits written by the CD `promote-gitops` job |
