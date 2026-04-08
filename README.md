# Cricket Match Analysis Agent

A practical cricket project to learn **agentic AI concepts** using a real observe-recall-evaluate-act strategy loop.

## Architecture (v2 — API + React)

```
backend/
  main.py           # FastAPI entry point — mounts routers, serves React dist
  core/             # Pure agent & domain logic (no HTTP knowledge)
    agent_core.py
    strategy_engine.py
    data_source.py
    history_store.py
    prematch_advisor.py
  services/         # Service-manager layer (orchestration, short-lived cache)
    match_service.py
    analysis_service.py
  routers/          # Thin FastAPI route handlers
    matches.py      # GET /api/matches/…
    analysis.py     # POST /api/analysis/
    history.py      # GET /api/history/…
  data/             # Runtime JSONL history
  requirements.txt

frontend/           # React + Vite UI
  src/
    App.jsx
    api/client.js
    components/
      MatchSelector.jsx
      MatchSnapshot.jsx
      MetricsPanel.jsx
      AgentLoop.jsx
      StrategyPanel.jsx
      ReflectionPanel.jsx
      PreMatchAdvisor.jsx
      HistoryPanel.jsx
  package.json
  vite.config.js
```

## Scope
- Hardcoded match states (scenario presets)
- Cricbuzz live match adapter
- Rule-based strategy engine
- Win-probability heuristic
- FastAPI REST back-end
- React front-end (Vite)

## Quick start

### Backend
```bash
pip install -r backend/requirements.txt
uvicorn backend.main:app --reload --port 8000
```

API docs available at **http://localhost:8000/docs**

### Frontend (dev)
```bash
cd frontend
npm install
npm run dev        # proxies /api → http://localhost:8000
```

### Frontend (production build)
```bash
cd frontend && npm run build
# FastAPI now serves the React app from /
uvicorn backend.main:app --port 8000
```

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/matches/scenarios` | List hardcoded scenario names |
| GET | `/api/matches/scenarios/{name}` | Get state for a named scenario |
| GET | `/api/matches/live` | List live Cricbuzz matches |
| GET | `/api/matches/live/state` | Fetch live match state |
| POST | `/api/analysis/` | Run the full agent cycle |
| GET | `/api/history/{match_key}` | Get per-match over history |
| GET | `/health` | Health check |

## Agent loop
1. **Observe** the current live match state
2. **Recall** prior over-level memory from saved history
3. **Evaluate** whether the last recommendation worked
4. **Reflect** on whether it should become more aggressive or conservative
5. **Act** with fresh plans for batting and bowling

## History storage
Saved snapshots are written per-over to `backend/data/strategy_history.jsonl`.
Each entry includes a plain-English `change_reason`, e.g.:
> *Win probability dropped because of a wicket and dot-ball pressure in a low-scoring over.*

## Legacy interfaces (still functional)
- `app.py` — terminal CLI
- `streamlit_app.py` — Streamlit dashboard (requires `pip install streamlit`)

