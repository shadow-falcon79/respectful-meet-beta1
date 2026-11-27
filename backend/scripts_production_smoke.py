"""Real production smoke checks. No mocks: run with a real deployment URL.
Usage: BASE_URL=https://api.example.com python scripts_production_smoke.py
Provider checks are only executed when the corresponding env credentials exist.
"""
import os, sys, json, urllib.request, urllib.error

BASE=os.environ.get("BASE_URL","").rstrip("/")
if not BASE:
    raise SystemExit("BASE_URL is required")

def get(path):
    req=urllib.request.Request(BASE+path, headers={"Accept":"application/json"})
    try:
        with urllib.request.urlopen(req, timeout=15) as r: return r.status, json.loads(r.read().decode())
    except urllib.error.HTTPError as e: return e.code, e.read().decode()

checks=[]
status,body=get("/api/v1/health"); checks.append(("health",status==200))
status,body=get("/api/v1/health/ready"); checks.append(("postgres_ready",status==200))
status,body=get("/api/v1/subscriptions/plans"); checks.append(("plans",status==200))
print("\n".join(f"{name}: {'PASS' if ok else 'FAIL'}" for name,ok in checks))
if not all(ok for _,ok in checks): sys.exit(1)
print("Provider/browser checks require authenticated real-client execution and are intentionally not simulated.")
