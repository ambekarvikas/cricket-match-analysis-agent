import { useState, useEffect } from 'react';
import { matchesApi } from '../api/client.js';

export default function MatchSelector({ onStateSelected }) {
  const [mode, setMode] = useState('hardcoded');
  const [scenarios, setScenarios] = useState([]);
  const [scenario, setScenario] = useState('chase_pressure');
  const [liveMatches, setLiveMatches] = useState([]);
  const [liveRef, setLiveRef] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  useEffect(() => {
    matchesApi.listScenarios().then(setScenarios).catch(() => {});
  }, []);

  useEffect(() => {
    if (mode === 'live') {
      matchesApi.listLive().then(setLiveMatches).catch(() => setLiveMatches([]));
    }
  }, [mode]);

  async function handleLoad() {
    setLoading(true);
    setError(null);
    try {
      let state;
      if (mode === 'hardcoded') {
        state = await matchesApi.getScenario(scenario);
      } else {
        const ref = liveRef.trim() || (liveMatches[0]?.match_id ?? null);
        state = await matchesApi.getLiveState(ref || null);
      }
      onStateSelected(state);
    } catch (err) {
      setError(err.response?.data?.detail ?? err.message);
    } finally {
      setLoading(false);
    }
  }

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
      <div className="control-group">
        <label>Data source</label>
        <div className="radio-group">
          {['hardcoded', 'live'].map(m => (
            <label key={m}>
              <input type="radio" value={m} checked={mode === m} onChange={() => setMode(m)} />
              <span className="radio-option">{m === 'hardcoded' ? '📋 Hardcoded' : '📡 Live'}</span>
            </label>
          ))}
        </div>
      </div>

      {mode === 'hardcoded' ? (
        <div className="control-group">
          <label>Scenario</label>
          <select value={scenario} onChange={e => setScenario(e.target.value)}>
            {scenarios.map(s => <option key={s} value={s}>{s.replace(/_/g, ' ')}</option>)}
          </select>
        </div>
      ) : (
        <>
          {liveMatches.length > 0 && (
            <div className="control-group">
              <label>Detected live matches</label>
              <select value={liveRef} onChange={e => setLiveRef(e.target.value)}>
                <option value="">— first detected —</option>
                {liveMatches.map(m => (
                  <option key={m.match_id ?? m.source_url} value={m.match_id ?? m.source_url}>
                    {m.batting_team} vs {m.bowling_team} | {m.runs}/{m.wickets} ({m.overs})
                  </option>
                ))}
              </select>
            </div>
          )}
          <div className="control-group">
            <label>Or paste Cricbuzz URL / match_id</label>
            <input
              type="text"
              placeholder="https://www.cricbuzz.com/live-cricket-scores/..."
              value={liveRef}
              onChange={e => setLiveRef(e.target.value)}
            />
          </div>
        </>
      )}

      {error && <div className="alert error">{error}</div>}

      <button className="btn btn-primary" onClick={handleLoad} disabled={loading}>
        {loading ? 'Loading…' : '🔍 Analyse'}
      </button>
    </div>
  );
}
