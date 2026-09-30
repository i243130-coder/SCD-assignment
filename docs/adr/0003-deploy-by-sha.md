# ADR-0003: Deploy by SHA, then by signed digest

## Status
Accepted (amended: digest + Cosign)

## Context
Need reproducible deployments. `:latest` is ambiguous. A git-SHA tag is traceable, but a tag is still a mutable pointer: anyone with push rights can re-point `:<sha>` at a different image.

## Decision
Tag images with the git commit SHA for humans, but **deploy by content digest** (`image@sha256:…`), and only after the digest's **Cosign signature** verifies.

- `build-push` (cd.yml) pushes, then signs each digest keylessly with the workflow's GitHub OIDC identity (`id-token: write`, no long-lived key).
- `deploy-k8s` runs `cosign verify` with `--certificate-identity https://github.com/<owner>/SCD-assignment/.github/workflows/cd.yml@refs/heads/main` before anything is applied, then `kustomize edit set image …@<digest>`.
- `promote-gitops` writes the same verified digests to the GitOps overlay (ADR-0005).
- Base images are also pinned by digest (`FROM python:3.12-slim@sha256:…`), and every Action by commit SHA.

## Consequences
"What is production running?" is answered by a digest you can `docker pull` and a commit you can `git show`. An image not built by this repository's CD on `main` cannot pass verification. Rollback = redeploy (or `git revert` to) the previous digest. `:latest` is pushed for convenience but never deployed. Cost: digests are unreadable, so the CD run summary maps each digest to its source commit.
