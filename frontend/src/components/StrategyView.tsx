import type { AnalysisResult } from '../types'

interface StrategyViewProps {
  analysis: AnalysisResult
}

export function StrategyView({ analysis }: StrategyViewProps) {
  const { plan, state } = analysis
  return (
    <div className="bg-gray-900 rounded-lg p-4 border border-gray-800 space-y-3">
      <h2 className="text-base font-semibold text-emerald-400">Team Perspectives</h2>
      <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
        <div className="bg-emerald-900/20 border border-emerald-800 rounded-lg p-3 space-y-1">
          <h3 className="text-sm font-semibold text-emerald-300">
            Batting Plan — {state.batting_team ?? 'Batting'}
          </h3>
          <div className="text-base font-bold text-white">{plan.strategy}</div>
          <div className="text-xs text-gray-300">
            <span className="text-gray-400">Next Over Target: </span>
            <span className="font-mono">{plan.target_runs}</span>
          </div>
          <div className="text-xs text-gray-300">
            <span className="text-gray-400">Risk: </span>
            {plan.risk_level}
          </div>
          <div className="text-xs text-gray-300">
            <span className="text-gray-400">Focus: </span>
            {plan.focus}
          </div>
        </div>
        <div className="bg-amber-900/20 border border-amber-800 rounded-lg p-3 space-y-1">
          <h3 className="text-sm font-semibold text-amber-300">
            Bowling Counter-Plan — {state.bowling_team ?? 'Bowling'}
          </h3>
          <div className="text-base font-bold text-white">{plan.bowling_strategy ?? 'N/A'}</div>
          <div className="text-xs text-gray-300">
            <span className="text-gray-400">Risk: </span>
            {plan.bowling_risk_level ?? 'N/A'}
          </div>
          <div className="text-xs text-gray-300">
            <span className="text-gray-400">Focus: </span>
            {plan.bowling_focus ?? 'N/A'}
          </div>
        </div>
      </div>
      {plan.awareness_notes && plan.awareness_notes.length > 0 && (
        <div>
          <h4 className="text-xs font-semibold text-gray-400 mb-1">Key Facts</h4>
          <ul className="text-xs text-gray-300 space-y-0.5 list-disc list-inside">
            {plan.awareness_notes.map((note, i) => (
              <li key={i}>{note}</li>
            ))}
          </ul>
        </div>
      )}
    </div>
  )
}
