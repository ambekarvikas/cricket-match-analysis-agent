import { useCallback, useEffect, useState } from 'react'
import {
  fetchCurrentUser,
  fetchScenarios,
  getStoredAuthToken,
  loginUser,
  logoutUser,
  registerUser,
} from './api/client'
import { AgentLoop } from './components/AgentLoop'
import { AuthPanel } from './components/AuthPanel'
import { HistoryTable } from './components/HistoryTable'
import { MatchSnapshot } from './components/MatchSnapshot'
import { MetricsPanel } from './components/MetricsPanel'
import { PreMatchAdvisor } from './components/PreMatchAdvisor'
import { ReflectionPanel } from './components/ReflectionPanel'
import { SessionPanel } from './components/SessionPanel'
import { Sidebar } from './components/Sidebar'
import { StrategyView } from './components/StrategyView'
import { WhatIfPanel } from './components/WhatIfPanel'
import { useLiveMatches } from './hooks/useLiveMatches'
import { useMatchAnalysis } from './hooks/useMatchAnalysis'
import type { AuthUser, MatchState, SourceMode } from './types'

const LAST_LIVE_MATCH_KEY = 'cricket-analysis-last-live-match'

function getStoredLastLiveMatch(): string {
  if (typeof window === 'undefined') return ''
  return window.localStorage.getItem(LAST_LIVE_MATCH_KEY) ?? ''
}

function saveLastLiveMatch(reference: string): void {
  if (typeof window === 'undefined') return
  if (reference) {
    window.localStorage.setItem(LAST_LIVE_MATCH_KEY, reference)
  } else {
    window.localStorage.removeItem(LAST_LIVE_MATCH_KEY)
  }
}

function getMatchReferenceValue(match?: MatchState | null): string {
  const sourceUrl = typeof match?.source_url === 'string' ? match.source_url : ''
  const matchId = typeof match?.match_id === 'string' ? match.match_id : ''
  return sourceUrl || matchId || ''
}

export default function App() {
  const [mode, setMode] = useState<SourceMode>('live')
  const [scenario, setScenario] = useState('chase_pressure')
  const [scenarios, setScenarios] = useState<string[]>(['chase_pressure'])
  const [matchReference, setMatchReference] = useState(() => getStoredLastLiveMatch())
  const [autoRefresh, setAutoRefresh] = useState(false)
  const [refreshInterval, setRefreshInterval] = useState(30)
  const [currentUser, setCurrentUser] = useState<AuthUser | null>(null)
  const [authLoading, setAuthLoading] = useState(false)
  const [authError, setAuthError] = useState<string | null>(null)

  const { matches: liveMatches } = useLiveMatches()

  const handleMatchReferenceChange = useCallback((reference: string) => {
    setMatchReference(reference)
    saveLastLiveMatch(reference)
  }, [])

  useEffect(() => {
    fetchScenarios()
      .then(setScenarios)
      .catch(() => {})
  }, [])

  const { analysis, history, session, loading, error, refresh } = useMatchAnalysis({
    mode,
    scenario,
    matchReference: matchReference || undefined,
    autoRefresh,
    refreshInterval,
  })

  useEffect(() => {
    if (mode !== 'live' || liveMatches.length === 0) return

    const currentExists = matchReference
      ? liveMatches.some((match) => {
          const ref = getMatchReferenceValue(match)
          return ref === matchReference
        })
      : false

    if (!matchReference || !currentExists) {
      const fallbackReference = getMatchReferenceValue(liveMatches[0])
      if (fallbackReference && fallbackReference !== matchReference) {
        handleMatchReferenceChange(fallbackReference)
      }
    }
  }, [mode, liveMatches, matchReference, handleMatchReferenceChange])

  useEffect(() => {
    if (mode !== 'live' || !analysis) return
    const resolvedReference = getMatchReferenceValue(analysis.state)
    if (resolvedReference && resolvedReference !== matchReference) {
      handleMatchReferenceChange(resolvedReference)
    }
  }, [mode, analysis, matchReference, handleMatchReferenceChange])

  useEffect(() => {
    if (!getStoredAuthToken()) return
    setAuthLoading(true)
    fetchCurrentUser()
      .then((user) => {
        setCurrentUser(user)
        setAuthError(null)
      })
      .catch(() => {
        logoutUser()
        setCurrentUser(null)
      })
      .finally(() => setAuthLoading(false))
  }, [])

  const handleLogin = useCallback(async (email: string, password: string) => {
    setAuthLoading(true)
    setAuthError(null)
    try {
      const result = await loginUser(email, password)
      setCurrentUser(result.user)
      refresh()
    } catch (err: unknown) {
      setAuthError(err instanceof Error ? err.message : 'Login failed')
    } finally {
      setAuthLoading(false)
    }
  }, [refresh])

  const handleRegister = useCallback(async (email: string, password: string, displayName?: string) => {
    setAuthLoading(true)
    setAuthError(null)
    try {
      const result = await registerUser(email, password, displayName)
      setCurrentUser(result.user)
      refresh()
    } catch (err: unknown) {
      setAuthError(err instanceof Error ? err.message : 'Registration failed')
    } finally {
      setAuthLoading(false)
    }
  }, [refresh])

  const handleLogout = useCallback(() => {
    logoutUser()
    setCurrentUser(null)
    setAuthError(null)
    refresh()
  }, [refresh])

  return (
    <div className="flex min-h-screen">
      <Sidebar
        mode={mode}
        onModeChange={setMode}
        scenario={scenario}
        scenarios={scenarios}
        onScenarioChange={setScenario}
        matchReference={matchReference}
        onMatchReferenceChange={handleMatchReferenceChange}
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

        <AuthPanel
          user={currentUser}
          loading={authLoading}
          error={authError}
          onLogin={handleLogin}
          onRegister={handleRegister}
          onLogout={handleLogout}
        />

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
            <SessionPanel analysis={analysis} session={session} />
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
