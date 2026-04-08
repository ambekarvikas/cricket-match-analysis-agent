import { useEffect, useState } from 'react';
import {
  LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Legend,
} from 'recharts';
import { historyApi } from '../api/client.js';

const COL_LABELS = {
  timestamp: 'Time', score: 'Score', overs: 'Overs', phase: 'Phase',
  win_probability: 'Win %', strategy: 'Strategy', bowling_strategy: 'Bowling',
  target_runs: 'Target Runs', risk_level: 'Risk', agent_confidence: 'Confidence',
  change_reason: 'Insight',
};
const DISPLAY_COLS = Object.keys(COL_LABELS);

export default function HistoryPanel({ matchKey }) {
  const [rows, setRows] = useState([]);

  useEffect(() => {
    if (!matchKey) return;
    // Store chronological order (oldest first); API returns oldest-first already.
    historyApi.getHistory(matchKey, 50)
      .then(data => setRows(data))
      .catch(() => {});
  }, [matchKey]);

  if (!matchKey || rows.length === 0) return null;

  // rows is oldest→newest; charts use chronological order directly.
  const chartData = rows
    .filter(r => r.win_probability != null)
    .map(r => ({ overs: r.overs, 'Win %': r.win_probability }));

  const runsData = rows
    .filter(r => r.runs != null)
    .map(r => ({ overs: r.overs, Runs: r.runs }));

  // Table shows most-recent first.
  const displayRows = [...rows].reverse().map(r => {
    const obj = {};
    DISPLAY_COLS.forEach(c => { if (r[c] != null) obj[c] = String(r[c]); });
    return obj;
  });

  return (
    <div className="card">
      <div className="card-title">Previous Overs + Recommendation History</div>

      {chartData.length > 1 && (
        <>
          <p style={{ fontSize: '.78rem', color: 'var(--muted)', marginBottom: '.4rem' }}>Win % by Over</p>
          <div className="chart-wrap">
            <ResponsiveContainer width="100%" height={180}>
              <LineChart data={chartData}>
                <CartesianGrid strokeDasharray="3 3" stroke="#334155" />
                <XAxis dataKey="overs" stroke="#94a3b8" tick={{ fontSize: 11 }} />
                <YAxis stroke="#94a3b8" tick={{ fontSize: 11 }} domain={[0, 100]} />
                <Tooltip contentStyle={{ background: '#1e293b', border: '1px solid #334155' }} />
                <Line type="monotone" dataKey="Win %" stroke="#38bdf8" dot={false} strokeWidth={2} />
              </LineChart>
            </ResponsiveContainer>
          </div>
        </>
      )}

      {runsData.length > 1 && (
        <>
          <p style={{ fontSize: '.78rem', color: 'var(--muted)', margin: '.75rem 0 .4rem' }}>Runs by Over</p>
          <div className="chart-wrap">
            <ResponsiveContainer width="100%" height={140}>
              <LineChart data={runsData}>
                <CartesianGrid strokeDasharray="3 3" stroke="#334155" />
                <XAxis dataKey="overs" stroke="#94a3b8" tick={{ fontSize: 11 }} />
                <YAxis stroke="#94a3b8" tick={{ fontSize: 11 }} />
                <Tooltip contentStyle={{ background: '#1e293b', border: '1px solid #334155' }} />
                <Line type="monotone" dataKey="Runs" stroke="#4ade80" dot={false} strokeWidth={2} />
              </LineChart>
            </ResponsiveContainer>
          </div>
        </>
      )}

      <div className="table-wrap" style={{ marginTop: '.75rem' }}>
        <table>
          <thead>
            <tr>{DISPLAY_COLS.filter(c => displayRows.some(r => r[c])).map(c => (
              <th key={c}>{COL_LABELS[c]}</th>
            ))}</tr>
          </thead>
          <tbody>
            {displayRows.map((row, i) => (
              <tr key={i}>
                {DISPLAY_COLS.filter(c => displayRows.some(r => r[c])).map(c => (
                  <td key={c}>{row[c] ?? '—'}</td>
                ))}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
