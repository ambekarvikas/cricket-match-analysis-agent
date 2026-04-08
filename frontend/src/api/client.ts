import axios from 'axios'
import type { AnalysisResult, HistoryEntry, MatchState, PreMatchResult } from '../types'

const api = axios.create({ baseURL: '/api' })

export async function fetchScenarios(): Promise<string[]> {
  const { data } = await api.get<string[]>('/matches/scenarios')
  return data
}

export async function fetchScenarioState(name: string): Promise<MatchState> {
  const { data } = await api.get<MatchState>(`/matches/scenario/${name}`)
  return data
}

export async function fetchLiveMatches(): Promise<MatchState[]> {
  const { data } = await api.get<MatchState[]>('/matches/live')
  return data
}

export async function fetchLiveMatch(matchReference: string): Promise<MatchState> {
  const { data } = await api.get<MatchState>(`/matches/live/${encodeURIComponent(matchReference)}`)
  return data
}

export async function runAnalysis(state: MatchState): Promise<AnalysisResult> {
  const { data } = await api.post<AnalysisResult>('/analysis/run', { state })
  return data
}

export async function fetchPreMatch(state: MatchState): Promise<PreMatchResult> {
  const { data } = await api.post<PreMatchResult>('/analysis/prematch', { state })
  return data
}

export async function fetchHistory(matchKey: string, limit = 50): Promise<HistoryEntry[]> {
  const { data } = await api.get<{ match_key: string; entries: HistoryEntry[] }>(
    `/history/${encodeURIComponent(matchKey)}`,
    { params: { limit } }
  )
  return data.entries
}
