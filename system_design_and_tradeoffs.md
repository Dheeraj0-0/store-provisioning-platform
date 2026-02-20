# System Design & Tradeoffs (Round 1)

## Architecture

Flow:
`Dashboard -> FastAPI Orchestrator -> Helm CLI -> Kubernetes API`

Each store gets its own namespace (`store-<name>`) for isolation.

### Components

- **Dashboard**
  - Lists stores and statuses.
  - Creates/deletes stores.
- **FastAPI Orchestrator**
  - Validates requests.
  - Creates namespaces.
  - Executes idempotent `helm upgrade --install`.
  - Deletes stores via `helm uninstall` + namespace deletion.
- **Helm Chart (WooCommerce engine)**
  - WordPress Deployment + Service
  - MySQL Deployment + Service + PVC
  - Ingress for stable URL
  - Secret for DB credentials
  - Readiness/liveness probes
  - ResourceQuota and LimitRange

## Provisioning Lifecycle

1. User submits create-store request.
2. Orchestrator validates naming and engine.
3. Namespace is created/labeled with engine metadata.
4. Orchestrator generates random DB/admin credentials.
5. Helm release is installed/upgraded in target namespace.
6. Dashboard polls status from pod phase/readiness.

Statuses:
- **Provisioning**: pods not fully ready yet.
- **Ready**: all containers are running and ready.
- **Failed**: pod failure detected or API fetch issue.

## Isolation Strategy

- Namespace-per-store (preferred baseline).
- ResourceQuota + LimitRange to reduce noisy-neighbor risk.
- Separate PVC per store for DB persistence.

## Security Decisions

- Avoid hardcoded secrets in chart defaults.
- Generate sensitive values at runtime in orchestrator.
- Keep secrets in K8s Secret object (can be upgraded to external secret manager later).

## Reliability & Idempotency

- `helm upgrade --install` provides idempotent provisioning behavior.
- Deletion ignores missing Helm release errors and ensures namespace removal.

## Tradeoffs

- **Using shell calls to helm/kubectl** is simple and interview-friendly, but less robust than using Kubernetes/Helm SDKs.
- **Synchronous provisioning** (`--wait`) improves deterministic behavior, but can block API longer under slow cluster startup.
- **Single engine implemented (WooCommerce)** to maximize completeness for round-1 scope.
- **Medusa stub** is explicit and keeps interface future-compatible without partial unstable deployment logic.

## Scaling Strategy (Round 1 -> Round 2)

- Add async task queue for provisioning (Celery/Redis or Kubernetes Jobs).
- Add distributed lock/concurrency controls per store name.
- Add metrics and event logs for each lifecycle step.
- Extend chart strategy to support multiple engines with engine-specific subcharts.
- Add safe Helm upgrade/rollback API endpoints.
