import {
  CartesianGrid,
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts'
import type { HistoryEntry } from '../types'

interface HistoryTableProps {
  entries: HistoryEntry[]
  matchKey: string
}

export function HistoryTable({ entries, matchKey }: HistoryTableProps) {
  if (entries.length === 0) {
    return (
      <div className="bg-gray-900 rounded-lg p-4 border border-gray-800">
        <h2 className="text-base font-semibold text-emerald-400 mb-2">History</h2>
        <p className="text-xs text-gray-400">No saved history yet for match {matchKey}.</p>
      </div>
    )
  }

  const sorted = [...entries].sort((a, b) => {
    const ta = a.timestamp ?? ''
    const tb = b.timestamp ?? ''
    return tb.localeCompare(ta)
  })

  const runsChartData = [...entries]
    .filter((e) => e.overs !== undefined && e.runs !== undefined)
    .sort((a, b) => (a.overs ?? 0) - (b.overs ?? 0))
    .map((e) => ({ overs: e.overs, runs: e.runs }))

  const winChartData = [...entries]
    .filter((e) => e.overs !== undefined && e.win_probability !== undefined)
    .sort((a, b) => (a.overs ?? 0) - (b.overs ?? 0))
    .map((e) => ({ overs: e.overs, win_probability: e.win_probability }))

  const battingTeam = entries[entries.length - 1]?.batting_team ?? 'Team'

  const cols = [
    'timestamp',
    'score',
    'overs',
    'phase',
    'win_probability',
    'strategy',
    'target_runs',
    'risk_level',
    'agent_confidence',
    'change_reason',
  ] as const

  return (
    <div className="bg-gray-900 rounded-lg p-4 border border-gray-800 space-y-5">
      <h2 className="text-base font-semibold text-emerald-400">Previous Overs + Recommendation History</h2>

      <div className="overflow-x-auto">
        <table className="min-w-full text-xs text-gray-300">
          <thead>
            <tr>
              {cols.map((c) => (
                <th
                  key={c}
                  className="text-left text-gray-500 font-medium px-2 py-1 whitespace-nowrap border-b border-gray-800"
                >
                  {c.replace(/_/g, ' ')}
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {sorted.map((entry, i) => (
              <tr key={i} className="hover:bg-gray-800">
                {cols.map((c) => (
                  <td key={c} className="px-2 py-1 whitespace-nowrap max-w-xs truncate">
                    {entry[c] !== undefined && entry[c] !== null ? String(entry[c]) : '—'}
                  </td>
                ))}
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {runsChartData.length > 1 && (
        <div>
          <h3 className="text-xs font-semibold text-gray-400 mb-2">Runs by Over</h3>
          <ResponsiveContainer width="100%" height={160}>
            <LineChart data={runsChartData}>
              <CartesianGrid stroke="#374151" strokeDasharray="3 3" />
              <XAxis dataKey="overs" tick={{ fontSize: 10, fill: '#9ca3af' }} />
              <YAxis tick={{ fontSize: 10, fill: '#9ca3af' }} />
              <Tooltip contentStyle={{ backgroundColor: '#111827', border: '1px solid #374151', fontSize: 11 }} />
              <Line type="monotone" dataKey="runs" stroke="#34d399" dot={false} strokeWidth={2} />
            </LineChart>
          </ResponsiveContainer>
        </div>
      )}

      {winChartData.length > 1 && (
        <div>
          <h3 className="text-xs font-semibold text-gray-400 mb-2">{battingTeam} Win % by Over</h3>
          <ResponsiveContainer width="100%" height={160}>
            <LineChart data={winChartData}>
              <CartesianGrid stroke="#374151" strokeDasharray="3 3" />
              <XAxis dataKey="overs" tick={{ fontSize: 10, fill: '#9ca3af' }} />
              <YAxis domain={[0, 100]} tick={{ fontSize: 10, fill: '#9ca3af' }} />
              <Tooltip contentStyle={{ backgroundColor: '#111827', border: '1px solid #374151', fontSize: 11 }} />
              <Line type="monotone" dataKey="win_probability" stroke="#f59e0b" dot={false} strokeWidth={2} />
            </LineChart>
          </ResponsiveContainer>
        </div>
      )}
    </div>
  )
}
