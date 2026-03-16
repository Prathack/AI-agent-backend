# FleetSight — AI Rental Vehicle Price Intelligence

> Vision-Language-Model powered web agent that **ACTUALLY VISITS rental websites**, fills in search forms, captures screenshots, and uses Groq Vision API to extract REAL prices — not simulated data.

---

## How It Works (REAL DATA EXTRACTION)

1. **User searches** for rental truck prices (pickup location, drop-off, dates)
2. **Backend launches** Playwright browser for each rental provider in parallel
3. **Browser navigates** to rental company website (U-Haul, Penske, Budget, Ryder, Enterprise)
4. **Form filling** - enters pickup location, drop-off location, dates
5. **Screenshot capture** - takes full-page screenshot after search results load
6. **Groq Vision Analysis** - sends real screenshot to Groq's vision model (`llama-3.2-90b-vision-preview`)
7. **Price extraction** - AI extracts actual prices from the screenshot (NOT simulated)
8. **Results displayed** - real prices shown in dashboard with confidence scores

---

## Architecture

```
USER REQUEST (Location, Dates)
     │
     ▼
FastAPI Backend  ──►  Job Queue (in-memory)
     │
     ├───────────────────────────────────────┐
     ▼                                       ▼
AgentOrchestrator                   CacheManager (Redis)
     │                                       │
     ├── U-Haul Agent (browser)       cache hit? ──► return
     ├── Budget Truck Agent                  │
     ├── Penske Agent            
     └── Ryder Agent
           │
           ▼
    StealthBrowser (Playwright) ──► Website Navigation ──► Form Fill ──► Screenshot
           │
           ▼
    Groq Vision API (llama-3.2-90b-vision-preview) ──► REAL PRICE EXTRACTION
           │
           ▼
    JSON with actual prices + confidence
           │
           ▼
    Dashboard displays REAL DATA
```

---

## Setup Requirements

### 1. Environment Variables (.env)
```bash
GROQ_API_KEY=<your-groq-api-key>
```
Get your key at: https://console.groq.com

### 2. Install dependencies
```bash
pip install -r requirements.txt

# Install Playwright browsers (REQUIRED for website automation)
playwright install chromium
```

### 3. Critical Dependencies
- **playwright** — actual browser automation (visits real websites)
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

---

## Troubleshooting

### 1. Console Shows "FALLBACK DATA" Warning

**Problem**: You see `⚠️ Using FALLBACK data for [Provider Name]` in the console

**Causes**:
- Playwright browser failed to launch
- Website navigation timed out
- Form filling couldn't locate input fields
- Groq API returned an error
- No prices found in the screenshot

**Solutions**:
- Ensure `playwright install chromium` was run
- Check internet connection
- Verify `GROQ_API_KEY` is set in `.env`
- Try a different pickup/dropoff location
- Check browser console for form selector errors

### 2. Low Confidence Scores

**Problem**: Prices are extracted but confidence is < 0.7

**Causes**:
- Prices were partially visible or unclear in screenshot
- Website layout is complex or has overlays
- AI model struggled to parse the pricing structure

**Solutions**:
- This is expected behavior - low confidence indicates uncertain extraction
- Check the `raw_text` field to see what was actually found
- These results should be treated as approximate

### 3. Playwright Installation Issues

**Problem**: `ModuleNotFoundError: No module named 'playwright'`

**Solution**:
```bash
pip install -r requirements.txt
playwright install chromium
```

### 4. Groq API Errors  

**Problem**: Console shows `Groq API error 401` or `403`

**Solutions**:
- Verify API key is correct: `echo $GROQ_API_KEY`
- Get key from https://console.groq.com
- Check API key permissions
- Ensure `.env` file is in backend directory

### 5. Website Navigation Timeouts

**Problem**: "Failed to navigate to [URL]" or takes very long

**Causes**:
- Website is blocking automated access
- Network connectivity issues
- Website requires JavaScript rendering

**Note**: Some websites have anti-bot protection that may prevent scraping

---

## Understanding the Data Flow

### When you search for a rental price:

```
Frontend ──► Backend /api/search
                │
        Job ID returned
                │
Frontend polls ◄─── Backend /api/jobs/{id}
                │
        [U-Haul Agent] Browser Launches → Navigate → Screenshot → Groq Vision → Extract Price
        [Budget Agent] Browser Launches → Navigate → Screenshot → Groq Vision → Extract Price
        [Penske Agent] Browser Launches → Navigate → Screenshot → Groq Vision → Extract Price
        [Ryder Agent]  Browser Launches → Navigate → Screenshot → Groq Vision → Extract Price
                │
        Results aggregated
                │
Frontend displays ◄─── All prices (real or fallback)
```

### Real vs Fallback Data:

**REAL DATA**:
- ✅ Extracted from actual website screenshot
- ✅ Confidence score 0.7-1.0
- ✅ raw_text field contains source quote

**FALLBACK DATA**:  
- ⚠️ Generated when website scraping fails
- ⚠️ Confidence score 0.4-0.55
- ⚠️ **Not actual website prices**
- ⚠️ WARNING logged to console

Always check confidence scores to understand data reliability.

---

## Performance Notes

- Parallel agent execution: ~8-15 seconds for 4 providers
- Caching: Identical searches return results instantly (1 hour TTL)
- Browser overhead: ~2-3 seconds per agent for startup
- Screenshot analysis: ~1-2 seconds per image via Groq API

---

## License

MIT
