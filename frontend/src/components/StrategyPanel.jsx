export default function StrategyPanel({ plan, state }) {
  if (!plan) return null;

  return (
    <div className="card">
      <div className="card-title">Team Perspectives</div>
      <div className="strategy-grid">
        <div className="strategy-card batting">
          <h3>🏏 Batting Plan</h3>
          <div className="strategy-name">{plan.strategy}</div>
          <div className="strategy-detail">
            <div>Next over target: <span>{plan.target_runs}</span></div>
            <div>Risk level: <span>{plan.risk_level}</span></div>
            <div>Focus: {plan.focus}</div>
            <div style={{ marginTop: '.3rem', color: 'var(--muted)' }}>
              Team: <span>{state?.batting_team ?? '—'}</span>
            </div>
          </div>
        </div>

        <div className="strategy-card bowling">
          <h3>🎯 Bowling Counter-Plan</h3>
          <div className="strategy-name">{plan.bowling_strategy ?? 'N/A'}</div>
          <div className="strategy-detail">
            <div>Risk level: <span>{plan.bowling_risk_level ?? 'N/A'}</span></div>
            <div>Focus: {plan.bowling_focus ?? 'N/A'}</div>
            <div style={{ marginTop: '.3rem', color: 'var(--muted)' }}>
              Team: <span>{state?.bowling_team ?? '—'}</span>
            </div>
          </div>
        </div>
      </div>

      {plan.awareness_notes?.length > 0 && (
        <div style={{ marginTop: '.75rem' }}>
          <div className="card-title" style={{ marginBottom: '.4rem' }}>Key Facts</div>
          <ul style={{ paddingLeft: '1.1rem', fontSize: '.82rem', color: 'var(--muted)', lineHeight: 1.8 }}>
            {plan.awareness_notes.map((note, i) => <li key={i}>{note}</li>)}
          </ul>
        </div>
      )}
    </div>
  );
}
