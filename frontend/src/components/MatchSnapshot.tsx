import type { MatchState } from '../types'

interface MatchSnapshotProps {
  state: MatchState
}

export function MatchSnapshot({ state }: MatchSnapshotProps) {
  const totalOvers = state.total_overs ?? 20
  return (
    <div className="bg-gray-900 rounded-lg p-4 border border-gray-800">
      <h2 className="text-base font-semibold text-emerald-400 mb-3">Live Match Snapshot</h2>
      <div className="flex flex-wrap gap-x-8 gap-y-1 text-sm">
        <div>
          <span className="text-gray-400">Match: </span>
          <span className="font-medium">
            {state.batting_team ?? '?'} vs {state.bowling_team ?? '?'}
          </span>
        </div>
        {!state.is_pre_match && (
          <div>
            <span className="text-gray-400">Score: </span>
            <span className="font-mono font-medium">
              {state.runs}/{state.wickets} in {state.overs} ov
            </span>
          </div>
        )}
        {totalOvers !== 20 && (
          <div className="text-yellow-400 font-medium">
            ⚠ Rain-impacted: {totalOvers}-over game
          </div>
        )}
        {state.venue && (
          <div>
            <span className="text-gray-400">Venue: </span>
            <span>{state.venue}</span>
          </div>
        )}
        {(state.striker ?? state.bowler) && (
          <div className="w-full mt-1">
            <span className="text-gray-400">Matchup: </span>
            <span className="font-mono text-xs">
              {state.striker} {state.striker_score} | {state.non_striker} {state.non_striker_score}{' '}
              | Bowler: {state.bowler} {state.bowler_score}
            </span>
          </div>
        )}
        {state.conditions_note && (
          <div className="w-full text-yellow-300 text-xs mt-1">{state.conditions_note}</div>
        )}
        {state.source_url && (
          <div className="w-full text-xs mt-1">
            <a
              href={state.source_url}
              target="_blank"
              rel="noopener noreferrer"
              className="text-blue-400 hover:underline"
            >
              Cricbuzz source ↗
            </a>
          </div>
        )}
      </div>
    </div>
  )
}
