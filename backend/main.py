from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import subprocess
import time

app = FastAPI()

# ✅ CORS (React ↔ FastAPI)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

def run(cmd):
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        raise Exception(result.stderr)
    return result.stdout

def store_ready(ns):
    try:
        out = run([
            "kubectl", "get", "pods", "-n", ns,
            "-o", "jsonpath={.items[*].status.phase}"
        ])
        return all(p == "Running" for p in out.split())
    except:
        return False

@app.get("/health")
def health():
    return {"status": "ok"}

@app.get("/stores")
def list_stores():
    out = run(["kubectl", "get", "ns", "-o", "jsonpath={.items[*].metadata.name}"])
    stores = []

    for s in out.split():
        if s.startswith("store"):
            stores.append({
                "name": s,
                "status": "Ready" if store_ready(s) else "Provisioning",
                "url": f"http://{s}.local"
            })

    return stores


@app.post("/stores/{name}")
def create_store(name: str):
    try:
        run(["kubectl", "create", "namespace", name])
    except:
        pass

    try:
        run([
            "helm", "upgrade", "--install",
            name, "../store-chart",
            "-n", name,
            "--wait"   # ✅ important for stability
        ])
    except Exception as e:
        raise HTTPException(500, detail=str(e))

    return {"store": name, "status": "provisioning"}

@app.delete("/stores/{name}")
def delete_store(name: str):
    try:
        run(["helm", "uninstall", name, "-n", name])
        run(["kubectl", "delete", "namespace", name])
    except Exception as e:
        raise HTTPException(500, detail=str(e))

    return {"store": name, "status": "deleted"}
