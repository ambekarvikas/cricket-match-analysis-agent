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
  recommended_action?: string
  bowling_recommended_action?: string
  decision_window?: string
  priority?: string
  decision_rationale?: string[]
  avoid_now?: string[]
}

export interface WhatIfScenario {
  label: string
  summary: string
  projected_score: string
  win_probability: number
  win_probability_delta: number
  impact: string
  recommended_response?: string
  focus?: string
}

export interface SessionSummary {
  session_id: string
  match_key?: string
  snapshot_count: number
  latest_score?: string | null
  latest_phase?: string | null
  momentum_delta?: number
  trend_summary: string
  latest_recommendation?: string | null
  decision_window?: string | null
  best_scenario?: WhatIfScenario | null
  last_updated?: string | null
}

export interface SessionEntry {
  timestamp?: string
  session_id?: string
  match_key?: string
  score?: string
  overs?: number
  phase?: string
  win_probability?: number
  recommended_action?: string
  bowling_recommended_action?: string
  [key: string]: unknown
}

export interface SessionResult {
  session_id: string
  summary: SessionSummary
  entries: SessionEntry[]
}

export interface AuthUser {
  id: number
  email: string
  display_name?: string | null
  created_at?: string | null
}

export interface AuthResponse {
  access_token: string
  token_type: string
  user: AuthUser
}

export interface EngineMeta {
  mode?: string
  primary_engine?: string
  supporting_engine?: string | null
  fallback_used?: boolean
  fallback_reason?: string | null
  request_id?: string
  cache_status?: string
  timings_ms?: Record<string, number>
  warnings?: string[]
}

export interface AnalysisResult {
  match_key: string
  session_id?: string
  cache_status?: string
  session_summary?: SessionSummary | null
  engine_meta?: EngineMeta | null
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
  what_if?: WhatIfScenario[]
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
