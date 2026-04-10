import { useCallback, useEffect, useRef, useState } from 'react'
import { fetchHistory, fetchLiveMatch, fetchScenarioState, fetchSession, runAnalysis } from '../api/client'
import type { AnalysisResult, HistoryEntry, MatchState, SessionResult, SourceMode } from '../types'

interface UseMatchAnalysisOptions {
  mode: SourceMode
  scenario?: string
  matchReference?: string
  autoRefresh: boolean
  refreshInterval: number
}

interface UseMatchAnalysisResult {
  analysis: AnalysisResult | null
  history: HistoryEntry[]
  session: SessionResult | null
  loading: boolean
  error: string | null
  refresh: () => void
}

export function useMatchAnalysis({
  mode,
  scenario,
  matchReference,
  autoRefresh,
  refreshInterval,
}: UseMatchAnalysisOptions): UseMatchAnalysisResult {
  const [analysis, setAnalysis] = useState<AnalysisResult | null>(null)
  const [history, setHistory] = useState<HistoryEntry[]>([])
  const [session, setSession] = useState<SessionResult | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const timerRef = useRef<ReturnType<typeof setTimeout> | null>(null)
  const sessionIdRef = useRef<string | null>(null)

  const doFetch = useCallback(async () => {
    setLoading(true)
    setError(null)
    try {
      let state: MatchState
      if (mode === 'live') {
        state = await fetchLiveMatch(matchReference ?? '')
      } else {
        state = await fetchScenarioState(scenario ?? 'chase_pressure')
      }
      const result = await runAnalysis(state, sessionIdRef.current ?? undefined)
      setAnalysis(result)

      if (result.session_id) {
        sessionIdRef.current = result.session_id
        const sessionData = await fetchSession(result.session_id)
        setSession(sessionData)
      } else {
        setSession(null)
      }

      const hist = await fetchHistory(result.match_key)
      setHistory(hist)
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : 'Failed to load analysis')
    } finally {
      setLoading(false)
    }
  }, [mode, scenario, matchReference])

  const refresh = useCallback(() => {
    if (timerRef.current) clearTimeout(timerRef.current)
    void doFetch()
  }, [doFetch])

  useEffect(() => {
    sessionIdRef.current = null
    setSession(null)
  }, [mode, scenario, matchReference])

  useEffect(() => {
    void doFetch()
  }, [doFetch])

  useEffect(() => {
    if (!autoRefresh || mode !== 'live') return
    timerRef.current = setTimeout(() => {
      void doFetch()
    }, refreshInterval * 1000)
    return () => {
      if (timerRef.current) clearTimeout(timerRef.current)
    }
  }, [analysis, autoRefresh, mode, refreshInterval, doFetch])

  return { analysis, history, session, loading, error, refresh }
}
