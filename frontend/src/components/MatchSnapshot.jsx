export default function MatchSnapshot({ state }) {
  if (!state) return null;
  const totalOvers = state.total_overs ?? 20;

  return (
    <div className="card">
      <div className="card-title">Live Match Snapshot</div>
      <p style={{ fontSize: '1rem', fontWeight: 700, marginBottom: '.5rem' }}>
        {state.batting_team} <span style={{ color: 'var(--muted)' }}>vs</span> {state.bowling_team}
      </p>
      <p style={{ fontSize: '1.5rem', fontWeight: 800, color: 'var(--accent)', marginBottom: '.6rem' }}>
        {state.runs}/{state.wickets}
        <span style={{ fontSize: '1rem', color: 'var(--muted)', fontWeight: 500, marginLeft: '.5rem' }}>
          ({state.overs} ov)
        </span>
      </p>
      {totalOvers !== 20 && (
        <div className="alert warning" style={{ marginBottom: '.5rem' }}>
          Rain-impacted: reduced to {totalOvers} overs per side
        </div>
      )}
      {state.conditions_note && (
        <p style={{ fontSize: '.78rem', color: 'var(--muted)' }}>{state.conditions_note}</p>
      )}
      {(state.striker || state.bowler) && (
        <p style={{ fontSize: '.8rem', color: 'var(--muted)', marginTop: '.35rem' }}>
          <strong style={{ color: 'var(--text)' }}>Matchup: </strong>
          {state.striker} {state.striker_score} &amp;{' '}
          {state.non_striker} {state.non_striker_score} vs {state.bowler} {state.bowler_score}
        </p>
      )}
      {state.venue && (
        <p style={{ fontSize: '.78rem', color: 'var(--muted)', marginTop: '.25rem' }}>
          📍 {state.venue}
        </p>
      )}
    </div>
  );
}
