export default function ReflectionPanel({ result }) {
  if (!result?.reflection) return null;
  const { reflection } = result;

  return (
    <div className="card">
      <div className="card-title">Reflection Agent</div>
      <div className="reflection-grid">
        <div className="reflection-note">
          <strong>Previous Advice</strong>
          {reflection.verdict}
        </div>
        <div className="reflection-note">
          <strong>Batting Adjustment</strong>
          {reflection.batting_adjustment}
        </div>
        <div className="reflection-note">
          <strong>Bowling Adjustment</strong>
          {reflection.bowling_adjustment}
        </div>
      </div>
      <div className="alert info" style={{ marginTop: '.75rem' }}>
        {reflection.reflection}
      </div>
    </div>
  );
}
