# Cricket Match Analysis Agent

A practical cricket project to learn **agentic AI concepts** using a real observe-recall-evaluate-act strategy loop.

## Current scope
- hardcoded match states
- Cricbuzz live match adapter
- rule-based strategy engine
- win-probability heuristic
- terminal output

## Files
- `app.py` - terminal entry point with hardcoded or live mode
- `data_source.py` - hardcoded scenarios plus Cricbuzz live-feed parsing
- `strategy_engine.py` - state enrichment, strategy logic, explanation output

## Install
```bash
pip install -r requirements.txt
```

## Run terminal app
```bash
python app.py
```

## Run Streamlit dashboard
```bash
streamlit run streamlit_app.py
```

## Live mode flow
1. choose `2` in the CLI
2. let it detect the current cricket match from Cricbuzz
3. optionally paste a Cricbuzz match URL or `match_id`
4. enable **auto-refresh** if you want continuous updates
5. get the strategy recommendation for the current state every few seconds

## Auto-refresh mode
- press `Y` when asked to enable live auto-refresh
- default interval is `30` seconds
- minimum enforced interval is `10` seconds
- stop the loop anytime with `Ctrl+C`

## Agent loop
The app now behaves like a lightweight cricket agent:
1. **Observe** the current live match state
2. **Recall** prior over-level memory from saved history
3. **Evaluate** whether the last recommendation worked
4. **Reflect** on whether it should become more aggressive or more conservative
5. **Act** with fresh plans for both the batting team and the bowling team

## Example output
- pre-match toss recommendation for rain or dew conditions
- probable or confirmed playing XI from the source when available
- match snapshot
- batting-side and bowling-side win probability
- agent objective and confidence
- evaluation of the last recommendation
- reflection on whether the previous advice was correct
- batting plan and bowling counter-plan
- source URL for the live feed
- saved recommendation history by over with win% change reasons

## History storage
Saved snapshots are written to:
- `data/strategy_history.jsonl`

This now tracks the recommendation **over by over**, not ball by ball.
It also stores a plain-English `change_reason`, for example:
- `Win probability dropped because of a wicket and dot-ball pressure in a low-scoring over.`

## Suggested roadmap
1. improve rules using phase, wickets, and pressure
2. auto-refresh every 30-60 seconds
3. store previous overs and recommendations
4. add an LLM only for natural-language explanation
5. later convert into a multi-agent workflow

## Important note
Keep the **state schema** stable when you move from hardcoded data to live data. That will let you reuse the same strategy logic.

This live adapter is a **best-effort scraper**, since Cricbuzz does not expose an official public developer API for this use case.
