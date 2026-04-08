import { useCallback, useEffect, useRef, useState } from 'react'
import { fetchHistory, fetchLiveMatch, fetchScenarioState, runAnalysis } from '../api/client'
import type { AnalysisResult, HistoryEntry, MatchState, SourceMode } from '../types'

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
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const timerRef = useRef<ReturnType<typeof setTimeout> | null>(null)

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
      const result = await runAnalysis(state)
      setAnalysis(result)
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

  return { analysis, history, loading, error, refresh }
}
