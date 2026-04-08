export default function PreMatchAdvisor({ advice }) {
  if (!advice) return null;
  const { toss, recommended_xi, lineup } = advice;

  return (
    <div className="card">
      <div className="card-title">Pre-Match Advisor</div>

      <div className="metrics" style={{ marginBottom: '.75rem' }}>
        <div className="metric">
          <div className="metric-label">Toss Call</div>
          <div className="metric-value yellow">{toss.decision}</div>
        </div>
        <div className="metric">
          <div className="metric-label">Confidence</div>
          <div className="metric-value">{toss.confidence}</div>
        </div>
      </div>

      <p style={{ fontSize: '.83rem', color: 'var(--muted)', marginBottom: '.5rem' }}>
        <strong style={{ color: 'var(--text)' }}>Summary: </strong>{toss.summary}
      </p>
      {toss.reasons?.length > 0 && (
        <ul style={{ paddingLeft: '1.1rem', fontSize: '.8rem', color: 'var(--muted)', lineHeight: 1.8, marginBottom: '.75rem' }}>
          {toss.reasons.map((r, i) => <li key={i}>{r}</li>)}
        </ul>
      )}

      {recommended_xi?.teams && (
        <>
          <div className="card-title" style={{ marginBottom: '.4rem' }}>
            {recommended_xi.lineup_type ?? 'Agent Recommended XI'}
          </div>
          <div className="xi-grid">
            {Object.entries(recommended_xi.teams).map(([team, players]) => (
              <div key={team} className="xi-team">
                <h4>{team}</h4>
                {players.length > 0 ? (
                  <ul>{players.map(p => <li key={p}>{p}</li>)}</ul>
                ) : (
                  <p style={{ fontSize: '.78rem', color: 'var(--muted)' }}>
                    Not enough squad data for a full XI
                  </p>
                )}
              </div>
            ))}
          </div>
          {recommended_xi.reasoning?.length > 0 && (
            <ul style={{ marginTop: '.5rem', paddingLeft: '1.1rem', fontSize: '.78rem', color: 'var(--muted)', lineHeight: 1.8 }}>
              {recommended_xi.reasoning.map((r, i) => <li key={i}>{r}</li>)}
            </ul>
          )}
        </>
      )}

      {lineup?.teams && Object.values(lineup.teams).some(v => v.length > 0) && (
        <>
          <div className="card-title" style={{ margin: '.75rem 0 .4rem' }}>
            {lineup.lineup_type ?? 'Announced XI'}
          </div>
          <div className="xi-grid">
            {Object.entries(lineup.teams).map(([team, players]) => (
              players.length > 0 && (
                <div key={team} className="xi-team">
                  <h4>{team}</h4>
                  <ul>{players.map(p => <li key={p}>{p}</li>)}</ul>
                </div>
              )
            ))}
          </div>
        </>
      )}
    </div>
  );
}
