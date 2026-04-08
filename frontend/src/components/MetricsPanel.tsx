import type { MatchState } from '../types'

interface MetricCardProps {
  label: string
  value: string | number
  sub?: string
}

function MetricCard({ label, value, sub }: MetricCardProps) {
  return (
    <div className="bg-gray-900 border border-gray-800 rounded-lg p-3 text-center">
      <div className="text-xs text-gray-400 mb-1">{label}</div>
      <div className="text-lg font-bold text-white">{value}</div>
      {sub && <div className="text-xs text-gray-500 mt-0.5">{sub}</div>}
    </div>
  )
}

interface MetricsPanelProps {
  state: MatchState
}

export function MetricsPanel({ state }: MetricsPanelProps) {
  const rrr = state.required_run_rate
  const probability = state.estimated_win_probability
  const bowlingProb = state.estimated_bowling_win_probability
  const projected = state.projected_total
  const par = state.par_score

  return (
    <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
      <MetricCard
        label="Score"
        value={`${state.runs}/${state.wickets}`}
        sub={`${state.overs} ov`}
      />
      <MetricCard label="Phase" value={(state.phase ?? 'N/A').toUpperCase()} />
      <MetricCard label="Current RR" value={state.current_run_rate ?? 'N/A'} />
      <MetricCard label="Required RR" value={rrr !== undefined && rrr !== null ? rrr : 'N/A'} />
      <MetricCard label="Balls Left" value={state.balls_left ?? 'N/A'} />
      {state.target !== undefined && state.target !== null ? (
        <MetricCard label="Runs Needed" value={state.runs_needed ?? 'N/A'} />
      ) : (
        <MetricCard
          label="Projected Total"
          value={projected ?? state.runs}
          sub={par !== undefined ? `Par ${par}` : undefined}
        />
      )}
      <MetricCard
        label={`${state.batting_team ?? 'Batting'} Win %`}
        value={probability !== undefined && probability !== null ? `${probability}%` : 'N/A'}
      />
      <MetricCard
        label={`${state.bowling_team ?? 'Bowling'} Win %`}
        value={
          bowlingProb !== undefined && bowlingProb !== null ? `${bowlingProb}%` : 'N/A'
        }
      />
    </div>
  )
}
