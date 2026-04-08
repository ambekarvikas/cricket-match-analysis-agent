export interface MatchState {
  batting_team?: string
  bowling_team?: string
  innings?: number
  runs: number
  wickets: number
  overs: number
  target?: number
  total_overs?: number
  match_id?: string
  venue?: string
  status?: string
  source?: string
  source_url?: string
  is_pre_match?: boolean
  is_match_complete?: boolean
  is_innings_complete?: boolean
  result_summary?: string | null
  striker?: string
  striker_score?: string
  non_striker?: string
  non_striker_score?: string
  bowler?: string
  bowler_score?: string
  conditions_note?: string
  match_context?: string
  upcoming_phase_note?: string
  // enriched fields
  phase?: string
  current_run_rate?: number
  required_run_rate?: number
  runs_needed?: number
  balls_left?: number
  wickets_in_hand?: number
  estimated_win_probability?: number
  estimated_bowling_win_probability?: number
  projected_total?: number
  par_score?: number
  [key: string]: unknown
}

export interface ReasoningStep {
  step: string
  detail: string
}

export interface EvaluationResult {
  status: string
  headline: string
  detail: string
  batting_status?: string
  bowling_status?: string
  batting_headline?: string
  bowling_headline?: string
  batting_detail?: string
  bowling_detail?: string
  runs_scored?: number
  wickets_lost?: number
  overs_progress?: number
}

export interface ReflectionResult {
  verdict: string
  batting_adjustment: string
  bowling_adjustment: string
  reflection: string
}

export interface StrategyPlan {
  strategy: string
  target_runs?: string
  risk_level?: string
  focus?: string
  bowling_strategy?: string
  bowling_risk_level?: string
  bowling_focus?: string
  awareness_notes?: string[]
  batting_tactics?: string[]
  bowling_tactics?: string[]
  phase_watchouts?: string[]
  matchup_insights?: string[]
  current_batter_insight?: string
  current_bowler_insight?: string
}

export interface AnalysisResult {
  match_key: string
  state: MatchState
  plan: StrategyPlan
  objective: string
  observation: string
  memory: string
  evaluation: EvaluationResult
  reflection: ReflectionResult
  confidence: number
  action_summary: string
  reasoning_steps: ReasoningStep[]
  history_entry: Record<string, unknown>
  history_saved: boolean
}

export interface HistoryEntry {
  timestamp?: string
  match_key?: string
  batting_team?: string
  bowling_team?: string
  runs?: number
  wickets?: number
  score?: string
  overs?: number
  phase?: string
  win_probability?: number
  win_probability_delta?: number
  strategy?: string
  bowling_strategy?: string
  target_runs?: string
  risk_level?: string
  agent_confidence?: number
  change_reason?: string
  [key: string]: unknown
}

export interface TossRecommendation {
  decision: string
  confidence: string
  summary: string
  reasons: string[]
}

export interface PreMatchResult {
  toss: TossRecommendation
  recommended_xi: {
    lineup_type: string
    teams: Record<string, string[]>
    reasoning: string[]
    comparison_notes: Record<string, string[]>
  }
  lineup: {
    lineup_type: string
    teams: Record<string, string[]>
    source_url?: string
  }
}

export type SourceMode = 'live' | 'hardcoded'
