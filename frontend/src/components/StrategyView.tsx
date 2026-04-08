import type { AnalysisResult } from '../types'

interface StrategyViewProps {
  analysis: AnalysisResult
}

export function StrategyView({ analysis }: StrategyViewProps) {
  const { plan, state } = analysis

  const renderList = (title: string, items?: string[], accent = 'text-gray-400') => {
    if (!items || items.length === 0) return null
    return (
      <div>
        <h4 className={`text-xs font-semibold mb-1 ${accent}`}>{title}</h4>
        <ul className="text-xs text-gray-300 space-y-0.5 list-disc list-inside">
          {items.map((item, i) => (
            <li key={`${title}-${i}`}>{item}</li>
          ))}
        </ul>
      </div>
    )
  }

  return (
    <div className="bg-gray-900 rounded-lg p-4 border border-gray-800 space-y-3">
      <h2 className="text-base font-semibold text-emerald-400">Team Perspectives</h2>

      {state.upcoming_phase_note && (
        <div className="text-xs text-cyan-200 bg-cyan-900/20 border border-cyan-800 rounded-lg p-3">
          <span className="font-semibold">Upcoming phase read: </span>
          {state.upcoming_phase_note}
        </div>
      )}

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

      {(plan.current_batter_insight || plan.current_bowler_insight) && (
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
          {plan.current_batter_insight && (
            <div className="bg-gray-800 rounded-lg p-3 text-xs text-gray-200 border border-gray-700">
              <div className="text-emerald-300 font-semibold mb-1">Current Batter Insight</div>
              {plan.current_batter_insight}
            </div>
          )}
          {plan.current_bowler_insight && (
            <div className="bg-gray-800 rounded-lg p-3 text-xs text-gray-200 border border-gray-700">
              <div className="text-amber-300 font-semibold mb-1">Current Bowler Insight</div>
              {plan.current_bowler_insight}
            </div>
          )}
        </div>
      )}

      <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
        {renderList('Batting Tactics', plan.batting_tactics, 'text-emerald-300')}
        {renderList('Bowling Tactics', plan.bowling_tactics, 'text-amber-300')}
      </div>

      {renderList('Phase Watchouts', plan.phase_watchouts, 'text-cyan-300')}
      {renderList('Matchup Insights', plan.matchup_insights, 'text-purple-300')}
      {renderList('Key Facts', plan.awareness_notes)}
    </div>
  )
}
