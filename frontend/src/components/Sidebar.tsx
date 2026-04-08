import type { MatchState, SourceMode } from '../types'

interface SidebarProps {
  mode: SourceMode
  onModeChange: (m: SourceMode) => void
  scenario: string
  scenarios: string[]
  onScenarioChange: (s: string) => void
  matchReference: string
  onMatchReferenceChange: (r: string) => void
  liveMatches: MatchState[]
  autoRefresh: boolean
  onAutoRefreshChange: (v: boolean) => void
  refreshInterval: number
  onRefreshIntervalChange: (v: number) => void
  onRefreshNow: () => void
}

export function Sidebar({
  mode,
  onModeChange,
  scenario,
  scenarios,
  onScenarioChange,
  matchReference,
  onMatchReferenceChange,
  liveMatches,
  autoRefresh,
  onAutoRefreshChange,
  refreshInterval,
  onRefreshIntervalChange,
  onRefreshNow,
}: SidebarProps) {
  return (
    <aside className="w-72 shrink-0 bg-gray-900 border-r border-gray-800 p-5 flex flex-col gap-5">
      <h2 className="text-lg font-bold text-emerald-400">Controls</h2>

      <div>
        <label className="block text-xs text-gray-400 mb-1">Data source</label>
        <div className="flex gap-3">
          {(['live', 'hardcoded'] as SourceMode[]).map((m) => (
            <button
              key={m}
              onClick={() => onModeChange(m)}
              className={`flex-1 py-1.5 rounded text-sm font-medium transition-colors ${
                mode === m
                  ? 'bg-emerald-600 text-white'
                  : 'bg-gray-800 text-gray-300 hover:bg-gray-700'
              }`}
            >
              {m === 'live' ? 'Live Cricbuzz' : 'Hardcoded'}
            </button>
          ))}
        </div>
      </div>

      {mode === 'hardcoded' ? (
        <div>
          <label className="block text-xs text-gray-400 mb-1">Scenario</label>
          <select
            value={scenario}
            onChange={(e) => onScenarioChange(e.target.value)}
            className="w-full bg-gray-800 border border-gray-700 rounded px-2 py-1.5 text-sm text-gray-100"
          >
            {scenarios.map((s) => (
              <option key={s} value={s}>
                {s}
              </option>
            ))}
          </select>
        </div>
      ) : (
        <>
          <div>
            <label className="block text-xs text-gray-400 mb-1">
              Match URL / match_id / team name
            </label>
            <input
              type="text"
              value={matchReference}
              onChange={(e) => onMatchReferenceChange(e.target.value)}
              placeholder="Optional – leave blank for first detected"
              className="w-full bg-gray-800 border border-gray-700 rounded px-2 py-1.5 text-sm text-gray-100 placeholder-gray-600"
            />
          </div>
          {liveMatches.length > 0 && (
            <div>
              <label className="block text-xs text-gray-400 mb-1">Detected live matches</label>
              <ul className="text-xs text-gray-300 space-y-1 max-h-40 overflow-y-auto">
                {liveMatches.map((m, i) => (
                  <li
                    key={i}
                    className="cursor-pointer hover:text-emerald-400 truncate"
                    onClick={() =>
                      onMatchReferenceChange(
                        m.source_url ?? m.match_id ?? ''
                      )
                    }
                  >
                    {m.batting_team} vs {m.bowling_team} | {m.runs}/{m.wickets} ({m.overs})
                  </li>
                ))}
              </ul>
            </div>
          )}
        </>
      )}

      {mode === 'live' && (
        <div className="flex items-center gap-2">
          <input
            type="checkbox"
            id="autoRefresh"
            checked={autoRefresh}
            onChange={(e) => onAutoRefreshChange(e.target.checked)}
            className="accent-emerald-500"
          />
          <label htmlFor="autoRefresh" className="text-sm text-gray-300">
            Auto-refresh
          </label>
        </div>
      )}

      {mode === 'live' && autoRefresh && (
        <div>
          <label className="block text-xs text-gray-400 mb-1">
            Refresh interval: {refreshInterval}s
          </label>
          <input
            type="range"
            min={10}
            max={120}
            step={5}
            value={refreshInterval}
            onChange={(e) => onRefreshIntervalChange(Number(e.target.value))}
            className="w-full accent-emerald-500"
          />
        </div>
      )}

      <button
        onClick={onRefreshNow}
        className="mt-auto bg-emerald-700 hover:bg-emerald-600 text-white rounded py-2 text-sm font-medium transition-colors"
      >
        Refresh now
      </button>
    </aside>
  )
}
