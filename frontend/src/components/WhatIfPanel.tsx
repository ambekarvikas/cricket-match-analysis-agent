import type { WhatIfScenario } from '../types'

interface WhatIfPanelProps {
  scenarios: WhatIfScenario[]
}

export function WhatIfPanel({ scenarios }: WhatIfPanelProps) {
  if (!scenarios || scenarios.length === 0) return null

  const impactClass = (impact: string) => {
    if (impact.includes('positive')) return 'border-emerald-800 bg-emerald-900/20 text-emerald-200'
    if (impact.includes('negative')) return 'border-red-800 bg-red-900/20 text-red-200'
    if (impact.includes('closed')) return 'border-blue-800 bg-blue-900/20 text-blue-200'
    return 'border-gray-700 bg-gray-800 text-gray-200'
  }

  return (
    <div className="bg-gray-900 rounded-lg p-4 border border-gray-800 space-y-3">
      <h2 className="text-base font-semibold text-emerald-400">What-If Simulation</h2>
      <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-4 gap-3">
        {scenarios.map((scenario) => {
          const delta = scenario.win_probability_delta ?? 0
          const deltaText = `${delta >= 0 ? '+' : ''}${delta}%`
          return (
            <div
              key={scenario.label}
              className={`rounded-lg border p-3 space-y-2 ${impactClass(scenario.impact)}`}
            >
              <div className="flex items-start justify-between gap-2">
                <div className="text-sm font-semibold">{scenario.label}</div>
                <div className="text-[10px] uppercase tracking-wide opacity-80">{scenario.impact}</div>
              </div>
              <div className="text-xs opacity-90">{scenario.summary}</div>
              <div className="text-xs">
                <span className="opacity-75">Projected: </span>
                <span className="font-mono">{scenario.projected_score}</span>
              </div>
              <div className="text-xs">
                <span className="opacity-75">Win %: </span>
                <span className="font-semibold">{scenario.win_probability}%</span>
                <span className="ml-2 font-mono">({deltaText})</span>
              </div>
              {scenario.recommended_response && (
                <div className="text-[11px] opacity-80">
                  <span className="font-semibold">Likely agent response: </span>
                  {scenario.recommended_response}
                </div>
              )}
            </div>
          )
        })}
      </div>
    </div>
  )
}
