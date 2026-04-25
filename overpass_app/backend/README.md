# Overpass Recruiting Self-Contained Backend

This version removes the notebook dependency from runtime behavior.

The backend now owns:

- database initialization
- Overpass ingestion
- company storage
- website scraping
- company vector generation
- resume-to-company matching

## Project layout

```text
overpass_recruiting/
├── overpass_app/      # Vite frontend
└── backend/           # this FastAPI backend
```

## Setup

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
```

## Run

```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

## First workflow

### 1. Initialize tables
```bash
curl -X POST http://localhost:8000/api/admin/init-db
```

### 2. Ingest companies from Overpass
```bash
curl -X POST http://localhost:8000/api/admin/ingest-overpass   -H "Content-Type: application/json"   -d '{
    "south": 44.88,
    "west": -93.37,
    "north": 45.05,
    "east": -93.19,
    "name_filter": ".*",
    "office_filter": ".*"
  }'
```

### 3. Scrape company websites
```bash
curl -X POST http://localhost:8000/api/admin/scrape-websites   -H "Content-Type: application/json"   -d '{"limit": 100}'
```

### 4. Vectorize companies
```bash
curl -X POST http://localhost:8000/api/admin/vectorize-companies   -H "Content-Type: application/json"   -d '{"limit": 500}'
```

### 5. Score resume text
```bash
curl -X POST http://localhost:8000/api/matches/score-text   -H "Content-Type: application/json"   -d '{
    "resume_text": "Python SQL analytics healthcare operations dashboarding",
    "top_k": 5
  }'
```

## Current notes

- This is still an MVP backend, but it is self-contained.
- Scraping is intentionally simple right now: it fetches the website root URL only.
- Vectorization is intentionally simple right now: HashingVectorizer.
- The notebook is no longer required for runtime execution.
