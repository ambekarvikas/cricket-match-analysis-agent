import type { AnalysisResult } from '../types'

interface AgentLoopProps {
  analysis: AnalysisResult
}

export function AgentLoop({ analysis }: AgentLoopProps) {
  const { evaluation } = analysis

  const statusColor = (s: string) => {
    if (s.includes('complete') || s.includes('completed') || s.includes('break'))
      return 'text-cyan-400'
    if (s.includes('excellent') || s.includes('strong') || s.includes('on-track'))
      return 'text-emerald-400'
    if (s.includes('pressure') || s.includes('below')) return 'text-red-400'
    return 'text-yellow-400'
  }

  return (
    <div className="bg-gray-900 rounded-lg p-4 border border-gray-800 space-y-3">
      <h2 className="text-base font-semibold text-emerald-400">Agent Loop</h2>
      <div className="text-sm text-gray-200">
        <span className="text-gray-400 font-medium">Objective: </span>
        {analysis.objective}
      </div>

      <div className="grid grid-cols-2 sm:grid-cols-4 gap-2">
        {[
          { label: 'Confidence', value: `${analysis.confidence}%` },
          { label: 'Overall', value: evaluation.status.replace(/-/g, ' ') },
          { label: 'Batting Eval', value: evaluation.batting_status ?? 'N/A' },
          { label: 'Bowling Eval', value: evaluation.bowling_status ?? 'N/A' },
        ].map(({ label, value }) => (
          <div key={label} className="bg-gray-800 rounded p-2 text-center">
            <div className="text-xs text-gray-400">{label}</div>
            <div className={`text-sm font-semibold mt-0.5 ${statusColor(value)}`}>{value}</div>
          </div>
        ))}
      </div>

      <div className="space-y-1 text-xs text-gray-300">
        {evaluation.batting_detail && (
          <p>
            <span className="text-gray-400">Batting review: </span>
            {evaluation.batting_detail}
          </p>
        )}
        {evaluation.bowling_detail && (
          <p>
            <span className="text-gray-400">Bowling review: </span>
            {evaluation.bowling_detail}
          </p>
        )}
      </div>

      <div className="space-y-1">
        {analysis.reasoning_steps.map((step) => (
          <div key={step.step} className="text-xs">
            <span className="font-semibold text-emerald-300">{step.step}: </span>
            <span className="text-gray-300">{step.detail}</span>
          </div>
        ))}
      </div>
    </div>
  )
}
