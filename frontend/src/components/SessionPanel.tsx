import type { AnalysisResult, SessionResult } from '../types'

interface SessionPanelProps {
  analysis: AnalysisResult
  session: SessionResult | null
}

export function SessionPanel({ analysis, session }: SessionPanelProps) {
  if (!analysis.session_id) return null

  const summary = session?.summary ?? analysis.session_summary
  const recentEntries = session?.entries?.slice(-4).reverse() ?? []

  return (
    <div className="bg-gray-900 rounded-lg p-4 border border-gray-800 space-y-3">
      <div className="flex flex-wrap items-center justify-between gap-2">
        <h2 className="text-base font-semibold text-emerald-400">Session Context</h2>
        <div className="flex gap-2 text-[11px]">
          <span className="px-2 py-0.5 rounded bg-gray-800 text-gray-300">
            Session: {analysis.session_id}
          </span>
          {analysis.cache_status && (
            <span className={`px-2 py-0.5 rounded ${analysis.cache_status === 'hit' ? 'bg-blue-900/30 text-blue-300' : 'bg-amber-900/30 text-amber-300'}`}>
              Cache {analysis.cache_status}
            </span>
          )}
        </div>
      </div>

      {summary && (
        <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
          <div className="bg-gray-800 rounded-lg p-3 border border-gray-700">
            <div className="text-xs text-gray-400">Trend</div>
            <div className="text-xs text-gray-200 mt-1">{summary.trend_summary}</div>
          </div>
          <div className="bg-gray-800 rounded-lg p-3 border border-gray-700">
            <div className="text-xs text-gray-400">Session Depth</div>
            <div className="text-sm font-semibold text-white mt-1">
              {summary.snapshot_count ?? 0} snapshot(s)
            </div>
            <div className="text-xs text-gray-300 mt-1">
              Latest: {summary.latest_score ?? 'N/A'} · {summary.latest_phase ?? 'N/A'}
            </div>
          </div>
          <div className="bg-gray-800 rounded-lg p-3 border border-gray-700">
            <div className="text-xs text-gray-400">Best saved scenario</div>
            {summary.best_scenario ? (
              <>
                <div className="text-sm font-semibold text-emerald-300 mt-1">
                  {summary.best_scenario.label}
                </div>
                <div className="text-xs text-gray-300 mt-1">
                  Δ {summary.best_scenario.win_probability_delta}% · {summary.best_scenario.impact}
                </div>
              </>
            ) : (
              <div className="text-xs text-gray-300 mt-1">No saved scenario yet.</div>
            )}
          </div>
        </div>
      )}

      {recentEntries.length > 0 && (
        <div>
          <h3 className="text-xs font-semibold text-gray-400 mb-2">Recent session snapshots</h3>
          <div className="space-y-2">
            {recentEntries.map((entry, idx) => (
              <div key={`${entry.timestamp ?? idx}-${idx}`} className="bg-gray-800 rounded-lg p-2 border border-gray-700 text-xs text-gray-300">
                <div className="flex flex-wrap items-center gap-3">
                  <span className="font-mono text-white">{entry.score ?? 'N/A'}</span>
                  <span>{entry.overs ?? 'N/A'} ov</span>
                  <span>{entry.phase ?? 'N/A'}</span>
                  <span>WP {entry.win_probability ?? 'N/A'}%</span>
                </div>
                {entry.recommended_action && (
                  <div className="mt-1">
                    <span className="text-gray-400">Decision: </span>
                    {entry.recommended_action}
                  </div>
                )}
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  )
}
