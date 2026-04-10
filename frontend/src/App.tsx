import { useEffect, useState } from 'react'
import { fetchScenarios } from './api/client'
import { AgentLoop } from './components/AgentLoop'
import { HistoryTable } from './components/HistoryTable'
import { MatchSnapshot } from './components/MatchSnapshot'
import { MetricsPanel } from './components/MetricsPanel'
import { PreMatchAdvisor } from './components/PreMatchAdvisor'
import { ReflectionPanel } from './components/ReflectionPanel'
import { Sidebar } from './components/Sidebar'
import { StrategyView } from './components/StrategyView'
import { WhatIfPanel } from './components/WhatIfPanel'
import { useLiveMatches } from './hooks/useLiveMatches'
import { useMatchAnalysis } from './hooks/useMatchAnalysis'
import type { SourceMode } from './types'

export default function App() {
  const [mode, setMode] = useState<SourceMode>('hardcoded')
  const [scenario, setScenario] = useState('chase_pressure')
  const [scenarios, setScenarios] = useState<string[]>(['chase_pressure'])
  const [matchReference, setMatchReference] = useState('')
  const [autoRefresh, setAutoRefresh] = useState(false)
  const [refreshInterval, setRefreshInterval] = useState(30)

  const { matches: liveMatches } = useLiveMatches()

  useEffect(() => {
    fetchScenarios()
      .then(setScenarios)
      .catch(() => {})
  }, [])

  const { analysis, history, loading, error, refresh } = useMatchAnalysis({
    mode,
    scenario,
    matchReference: matchReference || undefined,
    autoRefresh,
    refreshInterval,
  })

  return (
    <div className="flex min-h-screen">
      <Sidebar
        mode={mode}
        onModeChange={setMode}
        scenario={scenario}
        scenarios={scenarios}
        onScenarioChange={setScenario}
        matchReference={matchReference}
        onMatchReferenceChange={setMatchReference}
        liveMatches={liveMatches}
        autoRefresh={autoRefresh}
        onAutoRefreshChange={setAutoRefresh}
        refreshInterval={refreshInterval}
        onRefreshIntervalChange={setRefreshInterval}
        onRefreshNow={refresh}
      />

      <main className="flex-1 p-6 overflow-y-auto space-y-5">
        <div className="flex items-center justify-between">
          <h1 className="text-2xl font-bold text-white">
            🏏 Cricket Match Analysis Agent
          </h1>
          {loading && (
            <span className="text-xs text-emerald-400 animate-pulse">Loading…</span>
          )}
        </div>

        {error && (
          <div className="bg-red-900/30 border border-red-700 rounded-lg p-3 text-sm text-red-300">
            {error}
          </div>
        )}

        {!analysis && !loading && !error && mode === 'live' && (
          <div className="bg-blue-900/20 border border-blue-700 rounded-lg p-3 text-sm text-blue-300">
            No active scored cricket match is available right now. Paste a Cricbuzz match URL/id, or
            switch to Hardcoded mode.
          </div>
        )}

        {analysis && (
          <>
            <MatchSnapshot state={analysis.state} />
            <PreMatchAdvisor state={analysis.state} />
            <MetricsPanel state={analysis.state} />
            <AgentLoop analysis={analysis} />
            <ReflectionPanel analysis={analysis} />
            <StrategyView analysis={analysis} />
            <WhatIfPanel scenarios={analysis.what_if ?? []} />
            {analysis.history_entry?.change_reason && (
              <div className="bg-blue-900/20 border border-blue-700 rounded-lg p-3 text-sm text-blue-200">
                <span className="font-semibold">Over-by-Over Insight: </span>
                {String(analysis.history_entry.change_reason)}
              </div>
            )}
            <HistoryTable entries={history} matchKey={analysis.match_key} />
            <div className="text-xs text-gray-600 text-right">
              Match key: {analysis.match_key}
            </div>
          </>
        )}
      </main>
    </div>
  )
}
