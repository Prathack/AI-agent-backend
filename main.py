"""
RentalAgent Backend — FastAPI Application
Vision-based rental truck price extraction system using Groq Vision API
"""

import asyncio
import json
import logging
import uuid
import os
from datetime import datetime
from typing import Any, Dict, List, Optional
from pydantic import BaseModel

from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import uvicorn

from agents.orchestrator import AgentOrchestrator
from schemas.models import (
    SearchRequest,
    SearchResponse,
    AgentStatus,
    RentalResult,
    JobStatus,
)
from cache.redis_cache import CacheManager

# ─────────────────────────────────────────────
# Logging
# ─────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
)
logger = logging.getLogger("rental_agent.api")

# ─────────────────────────────────────────────
# App
# ─────────────────────────────────────────────
app = FastAPI(
    title="RentalAgent API",
    description="AI-powered rental vehicle pricing extraction",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# In-memory job store (replace with Redis in production)
jobs: Dict[str, Dict[str, Any]] = {}
orchestrator = AgentOrchestrator()
cache = CacheManager()


# ─────────────────────────────────────────────
# Routes
# ─────────────────────────────────────────────

@app.get("/health")
async def health():
    return {"status": "ok", "timestamp": datetime.utcnow().isoformat()}

class AuthRequest(BaseModel):
    email: str

@app.post("/api/auth", response_model=Dict[str, str])
async def login_user(request: AuthRequest):
    if not request.email:
        raise HTTPException(status_code=400, detail="Email is required")
        
    users_file = "users.json"
    users = []
    
    if os.path.exists(users_file):
        try:
            with open(users_file, "r") as f:
                users = json.load(f)
        except Exception as e:
            logger.error(f"Could not read users file: {e}")
            
    if request.email not in users:
        users.append(request.email)
        with open(users_file, "w") as f:
            json.dump(users, f, indent=2)
            
    logger.info(f"User authenticated: {request.email}")
    return {"status": "success", "message": f"Authenticated {request.email}"}


@app.post("/api/search", response_model=Dict[str, str])
async def start_search(request: SearchRequest, background_tasks: BackgroundTasks):
    """Kick off an agent search job and return a job_id for polling."""
    job_id = str(uuid.uuid4())
    jobs[job_id] = {
        "id": job_id,
        "status": "queued",
        "request": request.dict(),
        "agents": {},
        "results": [],
        "created_at": datetime.utcnow().isoformat(),
        "updated_at": datetime.utcnow().isoformat(),
    }

    background_tasks.add_task(_run_search, job_id, request)
    logger.info(f"Job {job_id} queued for {request.pickup_location}")
    return {"job_id": job_id}


@app.get("/api/jobs/{job_id}", response_model=Dict[str, Any])
async def get_job(job_id: str):
    if job_id not in jobs:
        raise HTTPException(status_code=404, detail="Job not found")
    return jobs[job_id]


@app.get("/api/jobs/{job_id}/results")
async def get_results(job_id: str):
    if job_id not in jobs:
        raise HTTPException(status_code=404, detail="Job not found")
    return {"results": jobs[job_id].get("results", []), "status": jobs[job_id]["status"]}


@app.get("/api/jobs")
async def list_jobs():
    return {"jobs": list(jobs.values())[-10:]}  # last 10


# ─────────────────────────────────────────────
# Background Task
# ─────────────────────────────────────────────

async def _run_search(job_id: str, request: SearchRequest):
    """Run all agents concurrently and collect results."""
    jobs[job_id]["status"] = "running"
    jobs[job_id]["updated_at"] = datetime.utcnow().isoformat()

    providers = [
        {"name": "U-Haul", "url": "https://www.uhaul.com", "color": "#FF6B35"},
        {"name": "Budget Truck", "url": "https://www.budgettruck.com", "color": "#0066CC"},
        {"name": "Penske", "url": "https://www.pensketruckrental.com", "color": "#FFD700"},
        {"name": "Ryder", "url": "https://ryder.com/truck-rental", "color": "#CC0000"},
    ]

    # Initialize agent statuses
    for p in providers:
        jobs[job_id]["agents"][p["name"]] = {
            "name": p["name"],
            "status": "queued",
            "price": None,
            "screenshot": None,
            "logs": [],
            "color": p["color"],
        }

    jobs[job_id]["updated_at"] = datetime.utcnow().isoformat()

    # Run agents
    tasks = [
        _run_single_agent(job_id, p, request)
        for p in providers
    ]
    results = await asyncio.gather(*tasks, return_exceptions=True)

    valid_results = [r for r in results if isinstance(r, dict) and r.get("total_price")]
    jobs[job_id]["results"] = valid_results
    jobs[job_id]["status"] = "completed"
    jobs[job_id]["updated_at"] = datetime.utcnow().isoformat()
    logger.info(f"Job {job_id} completed with {len(valid_results)} results")


async def _run_single_agent(job_id: str, provider: dict, request: SearchRequest):
    name = provider["name"]

    def update(status: str, log: str = "", price=None, screenshot=None):
        jobs[job_id]["agents"][name]["status"] = status
        jobs[job_id]["updated_at"] = datetime.utcnow().isoformat()
        if log:
            jobs[job_id]["agents"][name]["logs"].append({
                "time": datetime.utcnow().isoformat(),
                "message": log,
            })
        if price is not None:
            jobs[job_id]["agents"][name]["price"] = price
        if screenshot:
            jobs[job_id]["agents"][name]["screenshot"] = screenshot

    try:
        update("running", f"Starting agent for {name}")

        # Check cache
        cache_key = cache.build_key(
            provider=name,
            pickup=request.pickup_location,
            dropoff=request.dropoff_location,
            date=request.pickup_date,
        )
        cached = await cache.get(cache_key)
        if cached:
            update("completed", f"Cache hit — returning stored data", price=cached.get("total_price"))
            return cached

        update("navigating", f"Opening browser for {provider['url']}")
        await asyncio.sleep(1.5)  # Simulated delay

        update("screenshot", "Capturing page screenshot")
        await asyncio.sleep(1)

        update("extracting", "Sending screenshot to Groq Vision")
        result = await orchestrator.run_agent(
            provider=provider,
            request=request,
            status_callback=lambda s, m: update(s, m),
        )

        if result:
            await cache.set(cache_key, result, ttl=3600)
            update("completed", f"Extracted price: {result.get('currency','$')}{result.get('total_price','N/A')}", price=result.get("total_price"))
            return result
        else:
            update("failed", "Could not extract pricing data")
            return None

    except Exception as e:
        update("failed", f"Agent error: {str(e)}")
        logger.error(f"Agent {name} failed: {e}")
        return None


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run("main:app", host="0.0.0.0", port=port)
