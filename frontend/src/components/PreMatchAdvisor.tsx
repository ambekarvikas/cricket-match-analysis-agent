import { useEffect, useState } from 'react'
import { fetchPreMatch } from '../api/client'
import type { MatchState, PreMatchResult } from '../types'

interface PreMatchAdvisorProps {
  state: MatchState
}

export function PreMatchAdvisor({ state }: PreMatchAdvisorProps) {
  const [advice, setAdvice] = useState<PreMatchResult | null>(null)
  const [loading, setLoading] = useState(false)

  useEffect(() => {
    let cancelled = false
    setLoading(true)
    fetchPreMatch(state)
      .then((data) => { if (!cancelled) setAdvice(data) })
      .catch(() => {})
      .finally(() => { if (!cancelled) setLoading(false) })
    return () => { cancelled = true }
  }, [state.batting_team, state.bowling_team, state.source_url])

  if (loading) return <div className="text-xs text-gray-400 p-4">Loading pre-match advice…</div>
  if (!advice) return null

  const { toss, recommended_xi, lineup } = advice

  return (
    <div className="bg-gray-900 rounded-lg p-4 border border-gray-800 space-y-4">
      <h2 className="text-base font-semibold text-emerald-400">Pre-Match Advisor</h2>
      <div className="flex flex-wrap gap-4">
        <div className="bg-gray-800 rounded p-3 min-w-[160px]">
          <div className="text-xs text-gray-400">Toss Call</div>
          <div className="text-base font-bold text-yellow-300">{toss.decision}</div>
          <div className="text-xs text-gray-400 mt-0.5">{toss.confidence} confidence</div>
        </div>
        <div className="text-xs text-gray-300 flex-1">
          <p className="text-gray-100 mb-1">{toss.summary}</p>
          {toss.reasons.map((r, i) => (
            <p key={i} className="text-gray-400">• {r}</p>
          ))}
        </div>
      </div>

      <TeamXISection
        title={recommended_xi.lineup_type}
        teams={recommended_xi.teams}
        emptyMsg="Agent needs more squad detail."
        reasoning={recommended_xi.reasoning}
        comparisonNotes={recommended_xi.comparison_notes}
      />
      {Object.values(lineup.teams).some((players) => players.length > 0) && (
        <TeamXISection
          title={lineup.lineup_type}
          teams={lineup.teams}
          emptyMsg="Lineup not available from source yet."
        />
      )}
    </div>
  )
}

function TeamXISection({
  title,
  teams,
  emptyMsg,
  reasoning,
  comparisonNotes,
}: {
  title: string
  teams: Record<string, string[]>
  emptyMsg: string
  reasoning?: string[]
  comparisonNotes?: Record<string, string[]>
}) {
  return (
    <div>
      <h3 className="text-xs font-semibold text-gray-400 mb-2">{title}</h3>
      <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
        {Object.entries(teams).map(([teamName, players]) => (
          <div key={teamName} className="bg-gray-800 rounded p-2">
            <div className="text-xs font-medium text-gray-200 mb-1">{teamName}</div>
            {players.length > 0 ? (
              <ol className="text-xs text-gray-300 space-y-0.5">
                {players.map((p, i) => (
                  <li key={i}>{i + 1}. {p}</li>
                ))}
              </ol>
            ) : (
              <p className="text-xs text-gray-500">{emptyMsg}</p>
            )}
          </div>
        ))}
      </div>
      {reasoning && reasoning.length > 0 && (
        <ul className="text-xs text-gray-400 mt-2 space-y-0.5">
          {reasoning.map((r, i) => (
            <li key={i}>• Selection logic: {r}</li>
          ))}
        </ul>
      )}
      {comparisonNotes &&
        Object.entries(comparisonNotes).map(([team, notes]) =>
          notes.map((n, i) => (
            <p key={`${team}-${i}`} className="text-xs text-gray-400">
              • {team}: {n}
            </p>
          ))
        )}
    </div>
  )
}
