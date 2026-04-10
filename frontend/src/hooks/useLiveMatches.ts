import { useEffect, useState } from 'react'
import { fetchLiveMatches } from '../api/client'
import type { MatchState } from '../types'

function isActiveLiveMatch(match: MatchState): boolean {
  if (match.is_pre_match || match.is_match_complete) return false

  const status = String(match.status ?? '').toLowerCase()
  const inactiveMarkers = ['preview', 'upcoming', 'scheduled', 'won by', 'no result', 'abandoned']
  if (inactiveMarkers.some((marker) => status.includes(marker))) return false

  return Number(match.runs ?? 0) > 0 || Number(match.overs ?? 0) > 0
}

export function useLiveMatches() {
  const [matches, setMatches] = useState<MatchState[]>([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    let cancelled = false
    setLoading(true)
    fetchLiveMatches()
      .then((data) => {
        if (!cancelled) {
          setMatches(data.filter(isActiveLiveMatch))
          setError(null)
        }
      })
      .catch((err: unknown) => {
        if (!cancelled) setError(err instanceof Error ? err.message : 'Unknown error')
      })
      .finally(() => {
        if (!cancelled) setLoading(false)
      })
    return () => { cancelled = true }
  }, [])

  return { matches, loading, error }
}
