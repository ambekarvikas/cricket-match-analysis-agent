import { useEffect, useState } from 'react'
import { fetchLiveMatches } from '../api/client'
import type { MatchState } from '../types'

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
          setMatches(data)
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
