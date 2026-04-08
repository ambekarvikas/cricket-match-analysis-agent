import type { AnalysisResult } from '../types'

interface ReflectionPanelProps {
  analysis: AnalysisResult
}

export function ReflectionPanel({ analysis }: ReflectionPanelProps) {
  const { reflection } = analysis
  return (
    <div className="bg-gray-900 rounded-lg p-4 border border-gray-800 space-y-3">
      <h2 className="text-base font-semibold text-emerald-400">Reflection Agent</h2>
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-2">
        {[
          { label: 'Previous Advice', value: reflection.verdict },
          { label: 'Batting Adjustment', value: reflection.batting_adjustment },
          { label: 'Bowling Adjustment', value: reflection.bowling_adjustment },
        ].map(({ label, value }) => (
          <div key={label} className="bg-gray-800 rounded p-2">
            <div className="text-xs text-gray-400">{label}</div>
            <div className="text-sm text-gray-100 mt-0.5">{value}</div>
          </div>
        ))}
      </div>
      <div className="text-xs text-gray-300 bg-gray-800 rounded p-3">{reflection.reflection}</div>
    </div>
  )
}
