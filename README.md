# Store Provisioning Platform (Round 1)

This project provisions **isolated ecommerce stores on Kubernetes using Helm** and exposes controls through a web dashboard.

Round-1 implementation focus:
- ✅ Fully implemented engine: **WooCommerce** (WordPress + MySQL)
- ✅ Stubbed engine: **MedusaJS** (API returns 501 with clear message)
- ✅ Namespace-per-store isolation
- ✅ Helm-driven provisioning and cleanup

## Repository Structure

- `backend/` – FastAPI orchestration API that calls `kubectl` + `helm`
- `web-dashboard/` – lightweight dashboard source code
- `store-chart/` – Helm chart for WooCommerce store stack
- `system_design_and_tradeoffs.md` – architecture and tradeoffs

## Prerequisites

- Python 3.10+
- Helm 3+
- kubectl
- A Kubernetes cluster: `kind`, `k3d`, `minikube`, `k3s`, or VPS cluster
- Ingress controller (nginx recommended)

## Local Setup

### 1) Start a local cluster (example: minikube)

```bash
minikube start
minikube addons enable ingress
```

### 2) Run backend orchestrator

```bash
cd backend
pip install -r requirements.txt
uvicorn main:app --reload
```

Backend runs on `http://127.0.0.1:8000`.

### 3) Run dashboard

```bash
cd web-dashboard
python -m http.server 3000
```

Dashboard runs on `http://127.0.0.1:3000`.

## API

- `GET /health`
- `GET /stores`
- `POST /stores/{name}` with JSON body `{ "engine": "woocommerce" | "medusa" }`
- `DELETE /stores/{name}`

Store names must start with `store-`.

## Helm Deployment Notes

Helm chart path: `store-chart/`

Resources included:
- Deployments: `wordpress`, `mysql`
- Services: `wordpress`, `mysql`
- Ingress for stable store URL
- PVC for MySQL persistence
- Secret for DB credentials
- Readiness + liveness probes
- ResourceQuota + LimitRange (isolation hardening)

### Values files

- `store-chart/values.local.yaml` – local cluster settings
- `store-chart/values.production.yaml` – production-like baseline

### Manual install example

```bash
kubectl create namespace store-demo
helm upgrade --install store-demo ./store-chart -n store-demo -f store-chart/values.local.yaml --set-string db.rootPassword='change-me'
```

## Functional Validation Checklist

WooCommerce flow:
1. Create a store via dashboard/API.
2. Open generated storefront URL.
3. Add product to cart.
4. Complete checkout.
5. Verify order in WordPress admin.

Medusa flow in round-1: API intentionally returns stub response (`501 Not Implemented`).

## Cleanup Guarantees

Store deletion flow executes:
1. `helm uninstall <store> -n <store>`
2. `kubectl delete namespace <store>`

This removes release resources and namespace-scoped artifacts safely.

## Security Highlights

- No hardcoded DB password in chart defaults.
- Backend generates random credentials at provisioning time.
- Secrets stored in Kubernetes Secret objects.

## Submission Assets

- Source code for dashboard, backend, and Helm chart
- Local and production values files
- System design/tradeoffs document

