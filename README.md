# FleetSight — AI Rental Vehicle Price Intelligence

> Vision-Language-Model powered web agent that extracts rental truck pricing from multiple providers simultaneously — no brittle CSS selectors, just AI eyes.

---

## Architecture

```
USER REQUEST
     │
     ▼
FastAPI Backend  ──►  Job Queue (in-memory / Redis)
     │
     ├──────────────────────────────────┐
     ▼                                  ▼
AgentOrchestrator              CacheManager (Redis)
     │                                  │
     ├── U-Haul Agent                   │
     ├── Budget Truck Agent     cache hit? ──► return stored result
     ├── Penske Agent
     └── Ryder Agent
           │
           ▼
    StealthBrowser (Playwright)
           │
           ▼
    Screenshot + DOM
           │
           ▼
    Groq Vision API (llama-4-scout-17b)
           │
           ▼
    Pydantic Validated JSON
           │
           ▼
    Dashboard (HTML/CSS/JS)
```

---

## Project Structure

```
rental-agent/
├── backend/
│   ├── main.py                  FastAPI application + job management
│   ├── requirements.txt
│   ├── agents/
│   │   └── orchestrator.py      Agent loop: observe → think → act
│   ├── browser/
│   │   └── stealth_browser.py   Playwright with anti-detection
│   ├── vision/
│   │   └── extractor.py         Groq Vision prompts + parsing
│   ├── schemas/
│   │   └── models.py            Pydantic models for validation
│   ├── cache/
│   │   └── redis_cache.py       TTL cache (Redis + memory fallback)
│   └── logs/
│       ├── screenshots/         Debug screenshots
│       └── debug/               Error captures
│
└── frontend/
    └── dashboard.html           Single-file dashboard (no build step)
```

---

## Quick Start

### 1. Backend

```bash
cd backend
pip install -r requirements.txt
playwright install chromium

# Set your Groq API key
export GROQ_API_KEY=your_groq_api_key_here

# Optional: Redis (falls back to memory if unavailable)
# docker run -d -p 6379:6379 redis

python main.py
# → http://localhost:8000
```

### 2. Frontend

Open `frontend/dashboard.html` directly in your browser.

> The dashboard works standalone (simulation mode) even without the backend running. When the backend is running on port 8000, it automatically connects to the real API.

---

## How It Works

### Vision-Based Extraction

Instead of fragile CSS selectors, the agent:

1. Launches a Playwright browser with stealth configuration
2. Navigates to the rental website
3. Captures a full-page screenshot
4. Sends the screenshot to **Groq's llama-4-scout-17b** vision model
5. Extracts structured pricing data from the model's response
6. Validates the result with Pydantic

```python
# Vision extraction prompt (simplified)
"""
Examine this rental website screenshot.
Extract: provider_name, vehicle_class, total_price, daily_rate, mileage_fee, currency.
Return ONLY valid JSON.
"""
```

### Self-Healing Agent Loop

```
Observe (screenshot) → Think (VLM analysis) → Act (click/type) → Observe…
```

If a button moves or the UI changes, the agent re-analyzes the screenshot and re-plans. No brittle selectors to break.

### Anti-Bot Measures

- Randomized user agents (Chrome, Firefox, Safari)
- Human-like mouse movement (random offset within element bounds)
- Realistic typing delays (50–180ms per keystroke)
- Random scroll behavior
- Navigator webdriver property masked via JS injection
- Realistic viewport sizes

### Caching

Results are cached by `provider:pickup:dropoff:date` key with a 1-hour TTL. Repeated searches within the window skip browser automation and LLM calls entirely.

```python
cache_key = cache.build_key(provider="U-Haul", pickup="New York, NY", ...)
cached = await cache.get(cache_key)  # Returns stored result if fresh
```

---

## API Reference

### POST /api/search
Start a new agent search job.

```json
{
  "pickup_location": "New York, NY",
  "dropoff_location": "Los Angeles, CA",
  "pickup_date": "2025-08-01",
  "return_date": "2025-08-07"
}
```

Returns: `{ "job_id": "uuid" }`

### GET /api/jobs/{job_id}
Poll job status. Returns agents, logs, and results.

### GET /api/jobs/{job_id}/results
Get final extracted results only.

---

## Configuration

| Variable | Default | Description |
|---|---|---|
| `GROQ_API_KEY` | — | **Required** for real extraction |
| `REDIS_URL` | `redis://localhost:6379` | Cache backend |
| `CACHE_TTL` | `3600` | Cache TTL in seconds |
| `HEADLESS` | `true` | Run browser headlessly |

---

## Extracted Data Schema

```json
{
  "provider_name": "U-Haul",
  "vehicle_class": "16ft Truck",
  "total_price": 189.99,
  "daily_rate": 39.99,
  "mileage_fee": 0.69,
  "currency": "USD",
  "availability": true,
  "confidence_score": 0.92,
  "pickup_location": "New York, NY",
  "dropoff_location": "Los Angeles, CA",
  "extracted_at": "2025-07-01T10:30:00Z"
}
```

---

## Extending

### Add a new provider

In `backend/agents/orchestrator.py`, the `_run_search` function defines the provider list:

```python
providers = [
    {"name": "U-Haul",        "url": "https://www.uhaul.com"},
    {"name": "Budget Truck",  "url": "https://www.budgettruck.com"},
    # Add new provider:
    {"name": "Enterprise",    "url": "https://www.enterprisetrucks.com"},
]
```

The agent loop handles it automatically — no selector writing needed.

---

## Tech Stack

| Layer | Technology |
|---|---|
| **Frontend** | HTML5, CSS3, Vanilla JS (no framework) |
| **Backend** | Python 3.11+, FastAPI, Uvicorn |
| **AI Vision** | Groq API (llama-4-scout-17b) |
| **Browser** | Playwright + stealth patches |
| **Validation** | Pydantic v2 |
| **Cache** | Redis (memory fallback) |
| **Logging** | Python structured logging |
