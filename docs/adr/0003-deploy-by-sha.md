# ADR-0003: Deploy by SHA

## Status
Accepted

## Context
Need reproducible deployments. `:latest` is ambiguous.

## Decision
Tag images with git commit SHA, deploy specific SHA.

## Consequences
Every deployment traceable to exact commit, rollback = redeploy previous SHA, `:latest` never deployed.
