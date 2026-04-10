import axios from 'axios'
import type {
  AnalysisResult,
  AuthResponse,
  AuthUser,
  HistoryEntry,
  MatchState,
  PreMatchResult,
  SessionResult,
} from '../types'

const TOKEN_KEY = 'cricket-analysis-token'
const api = axios.create({ baseURL: '/api' })

export function getStoredAuthToken(): string | null {
  if (typeof window === 'undefined') return null
  return window.localStorage.getItem(TOKEN_KEY)
}

export function setStoredAuthToken(token: string | null): void {
  if (typeof window !== 'undefined') {
    if (token) {
      window.localStorage.setItem(TOKEN_KEY, token)
    } else {
      window.localStorage.removeItem(TOKEN_KEY)
    }
  }
  if (token) {
    api.defaults.headers.common.Authorization = `Bearer ${token}`
  } else {
    delete api.defaults.headers.common.Authorization
  }
}

setStoredAuthToken(getStoredAuthToken())

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

export async function runAnalysis(state: MatchState, sessionId?: string): Promise<AnalysisResult> {
  const { data } = await api.post<AnalysisResult>('/analysis/run', {
    state,
    session_id: sessionId,
  })
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

export async function fetchSession(sessionId: string, limit = 30): Promise<SessionResult> {
  const { data } = await api.get<SessionResult>(`/session/${encodeURIComponent(sessionId)}`, {
    params: { limit },
  })
  return data
}

export async function registerUser(email: string, password: string, displayName?: string): Promise<AuthResponse> {
  const { data } = await api.post<AuthResponse>('/auth/register', {
    email,
    password,
    display_name: displayName,
  })
  setStoredAuthToken(data.access_token)
  return data
}

export async function loginUser(email: string, password: string): Promise<AuthResponse> {
  const { data } = await api.post<AuthResponse>('/auth/login', {
    email,
    password,
  })
  setStoredAuthToken(data.access_token)
  return data
}

export async function fetchCurrentUser(): Promise<AuthUser> {
  const { data } = await api.get<AuthUser>('/auth/me')
  return data
}

export function logoutUser(): void {
  setStoredAuthToken(null)
}
