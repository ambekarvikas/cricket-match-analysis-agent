export default function MetricsPanel({ state }) {
  if (!state) return null;

  const { batting_team, bowling_team, runs, wickets, phase, current_run_rate,
          required_run_rate, balls_left, runs_needed, target,
          estimated_win_probability, estimated_bowling_win_probability,
          projected_total, par_score } = state;

  const metrics = [
    { label: 'Score', value: `${runs}/${wickets}`, cls: 'blue' },
    { label: 'Phase', value: (phase ?? '').replace(/-/, ' ').toUpperCase() },
    { label: 'Current RR', value: current_run_rate ?? 'N/A' },
    { label: 'Required RR', value: required_run_rate ?? 'N/A' },
    { label: 'Balls Left', value: balls_left ?? 'N/A' },
    target != null
      ? { label: 'Runs Needed', value: runs_needed ?? 'N/A', cls: (runs_needed ?? 99) > (required_run_rate ?? 0) * 6 ? 'red' : 'green' }
      : { label: 'Projected', value: projected_total ?? runs, cls: '', extra: par_score != null ? `par ${par_score}` : null },
    { label: `${batting_team} Win%`, value: estimated_win_probability != null ? `${estimated_win_probability}%` : 'N/A', cls: 'green' },
    { label: `${bowling_team} Win%`, value: estimated_bowling_win_probability != null ? `${estimated_bowling_win_probability}%` : 'N/A', cls: 'red' },
  ];

  return (
    <div className="card">
      <div className="card-title">Match Metrics</div>
      <div className="metrics">
        {metrics.map(m => (
          <div key={m.label} className="metric">
            <div className="metric-label">{m.label}</div>
            <div className={`metric-value ${m.cls ?? ''}`}>{m.value}</div>
            {m.extra && <div style={{ fontSize: '.7rem', color: 'var(--muted)' }}>{m.extra}</div>}
          </div>
        ))}
      </div>
      {state.match_context && (
        <div className="alert info" style={{ marginTop: '.75rem' }}>{state.match_context}</div>
      )}
    </div>
  );
}
