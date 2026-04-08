import { useState, useCallback } from 'react';
import { analysisApi } from './api/client.js';
import MatchSelector from './components/MatchSelector.jsx';
import MatchSnapshot from './components/MatchSnapshot.jsx';
import MetricsPanel from './components/MetricsPanel.jsx';
import AgentLoop from './components/AgentLoop.jsx';
import StrategyPanel from './components/StrategyPanel.jsx';
import ReflectionPanel from './components/ReflectionPanel.jsx';
import PreMatchAdvisor from './components/PreMatchAdvisor.jsx';
import HistoryPanel from './components/HistoryPanel.jsx';

export default function App() {
  const [rawState, setRawState] = useState(null);
  const [result, setResult] = useState(null);
  const [analysing, setAnalysing] = useState(false);
  const [error, setError] = useState(null);

  const handleStateSelected = useCallback(async state => {
    setRawState(state);
    setError(null);
    setAnalysing(true);
    try {
      const data = await analysisApi.runAnalysis(state);
      setResult(data);
    } catch (err) {
      setError(err.response?.data?.detail ?? err.message);
    } finally {
      setAnalysing(false);
    }
  }, []);

  const handleRefresh = useCallback(async () => {
    if (!rawState) return;
    await handleStateSelected(rawState);
  }, [rawState, handleStateSelected]);

  return (
    <div className="app">
      <header className="header">
        <span style={{ fontSize: '1.5rem' }}>🏏</span>
        <h1>Cricket Match Analysis Agent</h1>
        <span className="badge">v2 · API</span>
        {result && (
          <button
            className="btn btn-secondary"
            style={{ marginLeft: 'auto' }}
            onClick={handleRefresh}
            disabled={analysing}
          >
            {analysing ? '⏳ Refreshing…' : '🔄 Refresh Analysis'}
          </button>
        )}
      </header>

      <div className="main">
        <aside className="sidebar">
          <MatchSelector onStateSelected={handleStateSelected} />

          {result && (
            <div style={{ fontSize: '.75rem', color: 'var(--muted)', marginTop: '.5rem' }}>
              <div>Match key: <code style={{ color: 'var(--accent)' }}>{result.match_key}</code></div>
              {result.history_saved
                ? <div style={{ color: 'var(--green)' }}>✓ New over snapshot saved</div>
                : <div>No new snapshot (same over)</div>}
            </div>
          )}
        </aside>

        <main className="content">
          {error && <div className="alert error">{error}</div>}

          {analysing && (
            <div style={{ textAlign: 'center', padding: '3rem 0' }}>
              <div className="spinner" />
              <p style={{ color: 'var(--muted)', marginTop: '1rem' }}>Running agent cycle…</p>
            </div>
          )}

          {!analysing && !result && (
            <div className="alert info" style={{ textAlign: 'center', padding: '2rem' }}>
              Select a data source and click <strong>Analyse</strong> to start.
            </div>
          )}

          {!analysing && result && (
            <>
              <MatchSnapshot state={rawState} />
              <MetricsPanel state={result.state} />
              {rawState?.is_pre_match && (
                <PreMatchAdvisor advice={result.pre_match_advice} />
              )}
              <StrategyPanel plan={result.plan} state={result.state} />
              <AgentLoop result={result} />
              <ReflectionPanel result={result} />
              {result.history_entry?.change_reason && (
                <div className="card">
                  <div className="card-title">Over-by-Over Insight</div>
                  <div className="alert info">{result.history_entry.change_reason}</div>
                </div>
              )}
              <HistoryPanel matchKey={result.match_key} />
            </>
          )}
        </main>
      </div>
    </div>
  );
}
