import { useState, type FormEvent } from 'react'
import type { AuthUser } from '../types'

interface AuthPanelProps {
  user: AuthUser | null
  loading: boolean
  error: string | null
  onLogin: (email: string, password: string) => Promise<void>
  onRegister: (email: string, password: string, displayName?: string) => Promise<void>
  onLogout: () => void
}

export function AuthPanel({ user, loading, error, onLogin, onRegister, onLogout }: AuthPanelProps) {
  const [mode, setMode] = useState<'login' | 'register'>('login')
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [displayName, setDisplayName] = useState('')

  const handleSubmit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault()
    if (mode === 'register') {
      await onRegister(email, password, displayName)
    } else {
      await onLogin(email, password)
    }
    setPassword('')
  }

  if (user) {
    return (
      <div className="bg-emerald-900/20 border border-emerald-800 rounded-lg p-3 text-sm text-emerald-100 space-y-2">
        <div className="flex items-center justify-between gap-3">
          <div>
            <div className="font-semibold">Signed in</div>
            <div className="text-xs text-emerald-200">
              {user.display_name || user.email}
            </div>
          </div>
          <button
            onClick={onLogout}
            className="px-3 py-1 rounded bg-emerald-700 hover:bg-emerald-600 text-white text-xs"
          >
            Logout
          </button>
        </div>
      </div>
    )
  }

  return (
    <div className="bg-gray-900 border border-gray-800 rounded-lg p-4 space-y-3">
      <div className="flex items-center justify-between">
        <h2 className="text-sm font-semibold text-emerald-400">Account</h2>
        <div className="flex gap-1 text-xs">
          {(['login', 'register'] as const).map((item) => (
            <button
              key={item}
              onClick={() => setMode(item)}
              className={`px-2 py-1 rounded ${
                mode === item ? 'bg-emerald-600 text-white' : 'bg-gray-800 text-gray-300'
              }`}
            >
              {item}
            </button>
          ))}
        </div>
      </div>

      <form onSubmit={(event) => void handleSubmit(event)} className="space-y-2">
        {mode === 'register' && (
          <input
            type="text"
            value={displayName}
            onChange={(e) => setDisplayName(e.target.value)}
            placeholder="Display name"
            className="w-full bg-gray-800 border border-gray-700 rounded px-2 py-1.5 text-sm text-gray-100"
          />
        )}
        <input
          type="email"
          value={email}
          onChange={(e) => setEmail(e.target.value)}
          placeholder="Email"
          className="w-full bg-gray-800 border border-gray-700 rounded px-2 py-1.5 text-sm text-gray-100"
        />
        <input
          type="password"
          value={password}
          onChange={(e) => setPassword(e.target.value)}
          placeholder="Password"
          className="w-full bg-gray-800 border border-gray-700 rounded px-2 py-1.5 text-sm text-gray-100"
        />
        <button
          type="submit"
          disabled={loading}
          className="w-full bg-emerald-700 hover:bg-emerald-600 disabled:opacity-60 text-white rounded py-2 text-sm font-medium"
        >
          {loading ? 'Please wait…' : mode === 'register' ? 'Create account' : 'Login'}
        </button>
      </form>

      {error && <div className="text-xs text-red-300">{error}</div>}
      <div className="text-[11px] text-gray-500">JWT is optional for browsing, but enables account-linked DB history.</div>
    </div>
  )
}
