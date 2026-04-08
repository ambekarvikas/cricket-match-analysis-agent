# Cricket Match Analysis Agent

A cricket strategy agent built on an **observe → recall → evaluate → reflect → act** loop, exposing a **FastAPI backend** and a **React + Vite frontend**.

---

## Architecture

```
cricket-match-analysis-agent/
├── backend/
│   ├── main.py                  # FastAPI app entry point (CORS, routers)
│   ├── api/
│   │   ├── routes/
│   │   │   ├── matches.py       # GET /api/matches/*
│   │   │   ├── analysis.py      # POST /api/analysis/*
│   │   │   └── history.py       # GET /api/history/*
│   │   └── schemas/             # Pydantic request/response models
│   ├── services/                # Service Manager layer
│   │   ├── match_service.py     # Orchestrates agent cycle + history
│   │   ├── data_service.py      # Wraps data_source
│   │   └── history_service.py   # Wraps history_store
│   ├── core/                    # Pure stateless agent logic
│   │   ├── agent_core.py
│   │   ├── strategy_engine.py
│   │   ├── prematch_advisor.py
│   │   ├── data_source.py
│   │   └── history_store.py
│   ├── data/                    # strategy_history.jsonl (persisted)
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── App.tsx
│   │   ├── api/client.ts        # Typed API wrappers
│   │   ├── hooks/               # useMatchAnalysis, useLiveMatches
│   │   └── components/          # Sidebar, MatchSnapshot, MetricsPanel,
│   │                            # AgentLoop, ReflectionPanel, StrategyView,
│   │                            # PreMatchAdvisor, HistoryTable
│   ├── package.json
│   └── vite.config.ts
├── app.py                       # (legacy) CLI entry point
├── streamlit_app.py             # (legacy) Streamlit UI
└── README.md
```

---

## API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| GET | `/health` | Health check |
| GET | `/api/matches/scenarios` | List hardcoded scenario names |
| GET | `/api/matches/scenario/{name}` | Get a hardcoded scenario state |
| GET | `/api/matches/live` | List live matches from Cricbuzz |
| GET | `/api/matches/live/{match_reference}` | Fetch a specific live match |
| POST | `/api/analysis/run` | Run agent cycle on a match state |
| POST | `/api/analysis/prematch` | Get pre-match advice (toss + XI) |
| GET | `/api/history/{match_key}` | Fetch over-by-over history |

---

## Running the Backend

```bash
cd backend
pip install -r requirements.txt
# from the repo root:
uvicorn backend.main:app --reload --port 8000
```

Interactive docs: http://localhost:8000/docs

---

## Running the Frontend

```bash
cd frontend
npm install
npm run dev
```

Open http://localhost:5173. The Vite dev server proxies `/api` → `http://localhost:8000`.

---

## Agent Loop

Each analysis request runs the full agent cycle:

1. **Observe** — read the current live or hardcoded match state
2. **Recall** — load prior over-level memory from `backend/data/strategy_history.jsonl`
3. **Evaluate** — score the last batting and bowling recommendation
4. **Reflect** — decide whether to adjust aggression or hold course
5. **Act** — produce a fresh batting plan and bowling counter-plan

---

## History Storage

Each completed over is saved to `backend/data/strategy_history.jsonl`.
Each entry contains the score, win probability, strategy, and a plain-English
`change_reason` explaining what shifted, e.g.:

> *Win probability dropped from 62% to 54% because a wicket fell and dot-ball pressure built up in a low-scoring over.*

---

## Legacy CLI / Streamlit

The original `app.py` (CLI) and `streamlit_app.py` are kept for reference.
They import from the root-level Python files which remain unchanged.

```bash
# CLI
pip install -r requirements.txt
python app.py

# Streamlit
streamlit run streamlit_app.py
```
