import { useState, type FormEvent } from 'react'
import { Sprout } from 'lucide-react'
import { api, type InviteInfo } from '../api'
import { N_, t } from '../i18n'

export type Invite = InviteInfo & { token: string }

type Props = { registrationOpen: boolean; invite?: Invite; notice?: string; onDone: () => void }

const ROLE_TEXT = { owner: N_('an owner'), member: N_('a member'), viewer: N_('a viewer') }

export default function Auth({ registrationOpen, invite, notice, onDone }: Props) {
  const canRegister = registrationOpen || !!invite
  const [mode, setMode] = useState<'login' | 'register'>(canRegister ? 'register' : 'login')
  const [username, setUsername] = useState('')
  const [displayName, setDisplayName] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState('')
  const [busy, setBusy] = useState(false)

  async function submit(e: FormEvent) {
    e.preventDefault()
    setBusy(true)
    setError('')
    try {
      if (mode === 'login') await api.login(username, password)
      else await api.register(username, password, displayName.trim(), invite?.token)
      onDone()
    } catch (err) {
      setError(err instanceof Error ? err.message : t('Something went wrong'))
    } finally {
      setBusy(false)
    }
  }

  const subtitle =
    mode === 'login'
      ? t('Welcome back.')
      : invite
        ? t("You're invited to join {household} as {role}.", { household: invite.household, role: t(ROLE_TEXT[invite.role]) })
        : t('Create your account to start planning.')

  return (
    <main className="mx-auto flex min-h-dvh max-w-sm flex-col justify-center gap-6 px-6">
      <header className="flex flex-col items-center gap-2 text-center">
        <Sprout className="size-12 text-leaf" aria-hidden />
        <h1 className="text-3xl font-extrabold">CropStack</h1>
        <p className="text-muted">{subtitle}</p>
      </header>

      {notice && (
        <p className="card text-sm" role="status">
          {notice}
        </p>
      )}

      <form className="card flex flex-col gap-4" onSubmit={submit}>
        {mode === 'register' && (
          <label className="field">
            <span>{t('Your name')}</span>
            <input
              className="input"
              autoComplete="name"
              maxLength={64}
              value={displayName}
              onChange={(e) => setDisplayName(e.target.value)}
            />
          </label>
        )}
        <label className="field">
          <span>{t('Username')}</span>
          <input
            className="input"
            autoComplete="username"
            autoCapitalize="none"
            required
            minLength={2}
            maxLength={64}
            value={username}
            onChange={(e) => setUsername(e.target.value)}
          />
        </label>
        <label className="field">
          <span>{t('Password')}</span>
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
          {mode === 'login' ? t('Log in') : invite ? t('Join {household}', { household: invite.household }) : t('Create account')}
        </button>
      </form>

      {canRegister && (
        <button
          className="text-sm text-leaf underline"
          onClick={() => setMode(mode === 'login' ? 'register' : 'login')}
        >
          {mode === 'login' ? t('Create an account instead') : t('I already have an account')}
        </button>
      )}
    </main>
  )
}
