export default function AgentLoop({ result }) {
  if (!result) return null;
  const { objective, evaluation, confidence, reasoning_steps } = result;

  const evalColor = status => {
    if (['strong', 'excellent', 'on-track'].includes(status)) return 'green';
    if (['under-pressure', 'below-target'].includes(status)) return 'red';
    return 'yellow';
  };

  return (
    <div className="card">
      <div className="card-title">Agent Loop</div>

      <p style={{ fontSize: '.85rem', marginBottom: '.75rem', color: 'var(--muted)' }}>
        <strong style={{ color: 'var(--text)' }}>Objective: </strong>{objective}
      </p>

      <div className="metrics" style={{ marginBottom: '1rem' }}>
        <div className="metric">
          <div className="metric-label">Confidence</div>
          <div className="metric-value blue">{confidence}%</div>
          <div className="conf-bar-bg" style={{ marginTop: '.4rem' }}>
            <div className="conf-bar" style={{ width: `${confidence}%` }} />
          </div>
        </div>
        <div className="metric">
          <div className="metric-label">Overall</div>
          <div className={`metric-value ${evalColor(evaluation?.status)}`}>
            {(evaluation?.status ?? 'n/a').replace(/-/g, ' ')}
          </div>
        </div>
        <div className="metric">
          <div className="metric-label">Batting eval</div>
          <div className={`metric-value ${evalColor(evaluation?.batting_status)}`}>
            {(evaluation?.batting_status ?? 'n/a').replace(/-/g, ' ')}
          </div>
        </div>
        <div className="metric">
          <div className="metric-label">Bowling eval</div>
          <div className={`metric-value ${evalColor(evaluation?.bowling_status)}`}>
            {(evaluation?.bowling_status ?? 'n/a').replace(/-/g, ' ')}
          </div>
        </div>
      </div>

      {evaluation?.batting_detail && (
        <p style={{ fontSize: '.8rem', color: 'var(--muted)', marginBottom: '.4rem' }}>
          <strong style={{ color: 'var(--text)' }}>Batting: </strong>{evaluation.batting_detail}
        </p>
      )}
      {evaluation?.bowling_detail && (
        <p style={{ fontSize: '.8rem', color: 'var(--muted)', marginBottom: '.75rem' }}>
          <strong style={{ color: 'var(--text)' }}>Bowling: </strong>{evaluation.bowling_detail}
        </p>
      )}

      <div className="steps">
        {(reasoning_steps ?? []).map(step => (
          <div key={step.step} className="step">
            <span className="step-label">{step.step}:</span>
            {step.detail}
          </div>
        ))}
      </div>
    </div>
  );
}
