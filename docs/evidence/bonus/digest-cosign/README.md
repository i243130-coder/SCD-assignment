# Evidence: deploy by digest + Cosign sign/verify (+3)

Steps in [../README.md](../README.md#evidence-3-digest--cosign-from-the-cd-run).

| File | What it shows |
|---|---|
| `cd-run.png` | CD run: test → build-push → deploy-k8s → promote-gitops, all green |
| `cosign-sign.png` | `build-push` → *Sign images by digest (keyless Cosign)* |
| `digests-summary.png` | run summary table with both `sha256:` digests |
| `cosign-verify.png` | `deploy-k8s` → *Verify image signatures* (`verified: …@sha256:…`) |
| `deploy-by-digest.png` | `deploy-k8s` → *Pin images by digest* (rendered `image: …@sha256:…`) |
| `running-images.txt` | pods in the cluster running `@sha256` images |
| `cosign-verify.txt` | local `cosign verify` output (if cosign is installed) |
