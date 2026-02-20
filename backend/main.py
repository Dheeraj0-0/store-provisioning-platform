from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum
import json
import secrets
import subprocess

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

app = FastAPI(title="Store Provisioning Orchestrator", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class StoreEngine(str, Enum):
    woocommerce = "woocommerce"
    medusa = "medusa"


class CreateStoreRequest(BaseModel):
    engine: StoreEngine = StoreEngine.woocommerce


class StoreResponse(BaseModel):
    name: str
    engine: str
    status: str
    url: str
    created_at: str | None = None


class CommandError(RuntimeError):
    pass


def run(cmd: list[str]) -> str:
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        raise CommandError(result.stderr.strip() or result.stdout.strip())
    return result.stdout.strip()


def namespace_exists(namespace: str) -> bool:
    result = subprocess.run(["kubectl", "get", "namespace", namespace], capture_output=True, text=True)
    return result.returncode == 0


def pod_health_status(namespace: str) -> str:
    try:
        raw = run(["kubectl", "get", "pods", "-n", namespace, "-o", "json"])
        data = json.loads(raw)
        items = data.get("items", [])
        if not items:
            return "Provisioning"

        phases = [item.get("status", {}).get("phase", "Unknown") for item in items]
        if any(phase == "Failed" for phase in phases):
            return "Failed"

        if all(phase == "Running" for phase in phases):
            ready_flags: list[bool] = []
            for item in items:
                statuses = item.get("status", {}).get("containerStatuses", [])
                ready_flags.extend(status.get("ready", False) for status in statuses)
            if ready_flags and all(ready_flags):
                return "Ready"
        return "Provisioning"
    except Exception:
        return "Failed"


def get_namespace_created_at(namespace: str) -> str | None:
    try:
        return run(["kubectl", "get", "namespace", namespace, "-o", "jsonpath={.metadata.creationTimestamp}"])
    except Exception:
        return None


def build_store_url(name: str) -> str:
    return f"http://{name}.localtest.me"


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/stores", response_model=list[StoreResponse])
def list_stores() -> list[StoreResponse]:
    raw = run(["kubectl", "get", "ns", "-o", "jsonpath={.items[*].metadata.name}"])
    stores: list[StoreResponse] = []

    for namespace in raw.split():
        if not namespace.startswith("store-"):
            continue

        engine = "woocommerce"
        try:
            engine = run([
                "kubectl",
                "get",
                "namespace",
                namespace,
                "-o",
                "jsonpath={.metadata.labels.store-engine}",
            ]) or "woocommerce"
        except Exception:
            pass

        stores.append(
            StoreResponse(
                name=namespace,
                engine=engine,
                status=pod_health_status(namespace),
                url=build_store_url(namespace),
                created_at=get_namespace_created_at(namespace),
            )
        )

    return sorted(stores, key=lambda s: s.created_at or "", reverse=True)


@app.post("/stores/{name}", response_model=StoreResponse)
def create_store(name: str, payload: CreateStoreRequest) -> StoreResponse:
    if not name.startswith("store-"):
        raise HTTPException(status_code=400, detail="Store name must start with 'store-'.")

    if payload.engine == StoreEngine.medusa:
        raise HTTPException(
            status_code=501,
            detail="Medusa provisioning is stubbed for round 1. Use engine=woocommerce.",
        )

    if not namespace_exists(name):
        run(["kubectl", "create", "namespace", name])

    run(["kubectl", "label", "namespace", name, "store-engine=woocommerce", "--overwrite"])

    generated_db_password = secrets.token_urlsafe(24)
    generated_wp_admin_password = secrets.token_urlsafe(24)

    try:
        run(
            [
                "helm",
                "upgrade",
                "--install",
                name,
                "../store-chart",
                "-n",
                name,
                "--wait",
                "--timeout",
                "10m",
                "--set-string",
                f"db.rootPassword={generated_db_password}",
                "--set-string",
                f"wordpress.adminPassword={generated_wp_admin_password}",
                "--set-string",
                f"ingress.host={name}.localtest.me",
            ]
        )
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc

    return StoreResponse(
        name=name,
        engine="woocommerce",
        status="Provisioning",
        url=build_store_url(name),
        created_at=datetime.now(timezone.utc).isoformat(),
    )


@app.delete("/stores/{name}")
def delete_store(name: str) -> dict[str, str]:
    try:
        if namespace_exists(name):
            subprocess.run(["helm", "uninstall", name, "-n", name], capture_output=True, text=True)
            run(["kubectl", "delete", "namespace", name, "--wait=true"])
        return {"store": name, "status": "deleted"}
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc
