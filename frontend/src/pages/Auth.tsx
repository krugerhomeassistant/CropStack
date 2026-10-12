import { useState, type FormEvent } from 'react'
import { Sprout } from 'lucide-react'
import { api, type InviteInfo } from '../api'
import { N_, t } from '../i18n'
import { Button, ErrorMessage } from '../components/ui'

export type Invite = InviteInfo & { token: string }

type Props = { registrationOpen: boolean; invite?: Invite; notice?: string; onDone: () => void }

/** An invite arrives as a link (.../invite/<token>) or the bare token: either way, the token is the last piece. */
const tokenOf = (pasted: string) => pasted.trim().split(/[/?#]/).filter(Boolean).pop() ?? ''

const ROLE_TEXT = { owner: N_('an owner'), member: N_('a member'), viewer: N_('a viewer') }

export default function Auth({ registrationOpen, invite, notice, onDone }: Props) {
  const canRegister = registrationOpen || !!invite
  const [mode, setMode] = useState<'login' | 'register'>(canRegister ? 'register' : 'login')
  const [username, setUsername] = useState('')
  const [displayName, setDisplayName] = useState('')
  const [password, setPassword] = useState('')
  const [join, setJoin] = useState(false) // sign up to join a household that sent an invite, instead of starting one
  const [code, setCode] = useState('')
  const [error, setError] = useState('')
  const [busy, setBusy] = useState(false)

  async function submit(e: FormEvent) {
    e.preventDefault()
    setBusy(true)
    setError('')
    try {
      if (mode === 'login') await api.login(username, password)
      else await api.register(username, password, displayName.trim(), invite?.token ?? (join ? tokenOf(code) : undefined))
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
    <main className="mx-auto flex min-h-dvh max-w-sm flex-col justify-center gap-6 px-4">
      <header className="flex flex-col items-center gap-2 text-center">
        <Sprout className="size-12 text-leaf" aria-hidden />
        <h1 className="text-[2.4375rem] leading-none font-extrabold">CropStack</h1>
        <p className="text-muted">{subtitle}</p>
      </header>

      {notice && (
        <p className="card text-sm" role="status">
          {notice}
        </p>
      )}

      <form className="card flex flex-col gap-4" onSubmit={submit}>
        {mode === 'register' && !invite && (
          <div role="radiogroup" aria-label={t('Household')} className="grid grid-cols-2 gap-2">
            {[false, true].map((j) => (
              <button
                key={String(j)}
                type="button"
                role="radio"
                aria-checked={join === j}
                onClick={() => setJoin(j)}
                className={`min-h-11 rounded-[var(--radius-row)] border px-3 text-sm font-semibold ${join === j ? 'border-leaf bg-leaf/15' : 'border-line bg-surface'}`}
              >
                {j ? t('Join a household') : t('Start my own')}
              </button>
            ))}
          </div>
        )}
        {mode === 'register' && join && !invite && (
          <label className="field">
            <span>{t('Invite link or code')}</span>
            <input className="input" required autoCapitalize="none" autoComplete="off" value={code} onChange={(e) => setCode(e.target.value)} />
            <span className="text-xs text-muted">{t('Ask a household owner for one: Household, then Create invite link.')}</span>
          </label>
        )}
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
        {error && <ErrorMessage>{error}</ErrorMessage>}
        <Button type="submit" disabled={busy}>
          {mode === 'login' ? t('Log in') : invite ? t('Join {household}', { household: invite.household }) : join ? t('Join household') : t('Create account')}
        </Button>
      </form>

      {canRegister && (
        <Button
          variant="ghost"
          className="self-center text-leaf"
          onClick={() => setMode(mode === 'login' ? 'register' : 'login')}
        >
          {mode === 'login' ? t('Create an account instead') : t('I already have an account')}
        </Button>
      )}
    </main>
  )
}
