# Kubernetes Store Provisioning Platform

A multi-tenant store provisioning system built using:

- React (Dashboard)
- FastAPI (Orchestrator API)
- Helm (Deployment templating)
- Kubernetes (Namespace-per-store isolation)
- WordPress + MySQL (Store engine)

---

## Architecture

User → React Dashboard → FastAPI → Helm → Kubernetes → Store Namespace

Each store runs in its own namespace with:

- Deployment (WordPress)
- Deployment (MySQL)
- Service
- Secret
- Persistent Storage

---

## Features

- Create store dynamically
- Delete store cleanly
- Multi-store isolation (namespace per store)
- Helm-based deployment
- Local Kubernetes (Minikube)
- Idempotent `helm upgrade --install`
- CORS enabled for dashboard
- Status detection (Provisioning / Ready)

---

## Local Setup

### 1. Start Kubernetes

'''
bash
minikube start

### 2. Start Backend
'''
cd backend
python -m uvicorn main:app --reload

Runs at:
http://127.0.0.1:8000

3. Start Dashboard
cd dashboard
npm install
npm start

Runs at:
http://localhost:3000
