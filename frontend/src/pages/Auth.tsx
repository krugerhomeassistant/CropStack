import { useState, type FormEvent } from 'react'
import { Sprout } from 'lucide-react'
import { api } from '../api'

type Props = { registrationOpen: boolean; onDone: () => void }

export default function Auth({ registrationOpen, onDone }: Props) {
  const [mode, setMode] = useState<'login' | 'register'>(registrationOpen ? 'register' : 'login')
  const [username, setUsername] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState('')
  const [busy, setBusy] = useState(false)

  async function submit(e: FormEvent) {
    e.preventDefault()
    setBusy(true)
    setError('')
    try {
      await (mode === 'login' ? api.login : api.register)(username, password)
      onDone()
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Something went wrong')
    } finally {
      setBusy(false)
    }
  }

  return (
    <main className="mx-auto flex min-h-dvh max-w-sm flex-col justify-center gap-6 px-6">
      <header className="flex flex-col items-center gap-2 text-center">
        <Sprout className="size-12 text-leaf" aria-hidden />
        <h1 className="text-3xl font-extrabold">CropStack</h1>
        <p className="text-muted">{mode === 'login' ? 'Welcome back.' : 'Create your account to start planning.'}</p>
      </header>

      <form className="card flex flex-col gap-4" onSubmit={submit}>
        <label className="field">
          <span>Username</span>
          <input
            className="input"
            autoComplete="username"
            required
            minLength={2}
            maxLength={64}
            value={username}
            onChange={(e) => setUsername(e.target.value)}
          />
        </label>
        <label className="field">
          <span>Password</span>
          <input
            className="input"
            type="password"
            autoComplete={mode === 'login' ? 'current-password' : 'new-password'}
            required
            minLength={8}
            value={password}
            onChange={(e) => setPassword(e.target.value)}
          />
        </label>
        {error && (
          <p className="text-sm text-red-600" role="alert">
            {error}
          </p>
        )}
        <button className="btn" disabled={busy}>
          {mode === 'login' ? 'Log in' : 'Create account'}
        </button>
      </form>

      {registrationOpen && (
        <button
          className="text-sm text-leaf underline"
          onClick={() => setMode(mode === 'login' ? 'register' : 'login')}
        >
          {mode === 'login' ? 'Create an account instead' : 'I already have an account'}
        </button>
      )}
    </main>
  )
}
