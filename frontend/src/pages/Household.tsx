import { useEffect, useState, type FormEvent } from 'react'
import { ArrowLeft, Copy, Link2, Trash2 } from 'lucide-react'
import { api, type Household as HouseholdData, type NewInvite, type PendingInvite, type Role, type User } from '../api'

const ROLES: { value: Role; label: string; hint: string }[] = [
  { value: 'member', label: 'Member', hint: 'Sees and does the daily tasks, logs harvests and notes' },
  { value: 'viewer', label: 'Viewer', hint: 'Can look, but not change anything' },
  { value: 'owner', label: 'Owner', hint: 'Everything, including the garden location and members' },
]

type Props = { user: User; onBack: () => void }

export default function Household({ user, onBack }: Props) {
  const [data, setData] = useState<HouseholdData | null>(null)
  const [invites, setInvites] = useState<PendingInvite[]>([])
  const [fresh, setFresh] = useState<NewInvite | null>(null)
  const [inviteRole, setInviteRole] = useState<Role>('member')
  const [name, setName] = useState('')
  const [confirmRemove, setConfirmRemove] = useState<number | null>(null)
  const [error, setError] = useState('')
  const isOwner = data?.my_role === 'owner'

  async function load() {
    try {
      const household = await api.household()
      setData(household)
      setName(household.name)
      if (household.my_role === 'owner') setInvites(await api.invites())
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load')
    }
  }

  useEffect(() => {
    load()
  }, [])

  async function run(action: () => Promise<unknown>) {
    setError('')
    try {
      await action()
      await load()
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Something went wrong')
    }
  }

  function rename(e: FormEvent) {
    e.preventDefault()
    run(() => api.renameHousehold(name.trim()))
  }

  async function invite() {
    setFresh(null)
    await run(async () => setFresh(await api.createInvite(inviteRole)))
  }

  const inviteUrl = fresh ? `${location.origin}${fresh.path}` : ''

  return (
    <main className="mx-auto flex min-h-dvh max-w-md flex-col gap-6 px-6 py-10">
      <header className="flex items-center gap-3">
        <button onClick={onBack} aria-label="Back" className="text-muted">
          <ArrowLeft className="size-5" aria-hidden />
        </button>
        <h1 className="text-2xl font-extrabold">Household</h1>
      </header>

      {error && (
        <p className="text-sm text-red-600" role="alert">
          {error}
        </p>
      )}

      {data && (
        <>
          <form className="card flex flex-col gap-3" onSubmit={rename}>
            <label className="field">
              <span>Household name</span>
              <input
                className="input"
                value={name}
                maxLength={80}
                required
                disabled={!isOwner}
                onChange={(e) => setName(e.target.value)}
              />
            </label>
            {isOwner && name.trim() !== data.name && <button className="btn">Save name</button>}
          </form>

          <section className="card flex flex-col gap-3" aria-labelledby="members-title">
            <h2 id="members-title" className="font-bold">
              People
            </h2>
            <ul className="flex flex-col divide-y divide-ink/10">
              {data.members.map((m) => (
                <li key={m.user_id} className="flex flex-wrap items-center gap-2 py-2">
                  <span className="min-w-0 flex-1">
                    <span className="font-semibold">{m.display_name || m.username}</span>
                    {m.user_id === user.id && <span className="text-sm text-muted"> (you)</span>}
                    <span className="block text-xs text-muted">@{m.username}</span>
                  </span>
                  {isOwner && m.user_id !== user.id ? (
                    <>
                      <label className="sr-only" htmlFor={`role-${m.user_id}`}>
                        Role for {m.display_name || m.username}
                      </label>
                      <select
                        id={`role-${m.user_id}`}
                        className="input w-auto py-1 text-sm"
                        value={m.role}
                        onChange={(e) => run(() => api.setRole(m.user_id, e.target.value as Role))}
                      >
                        {ROLES.map((r) => (
                          <option key={r.value} value={r.value}>
                            {r.label}
                          </option>
                        ))}
                      </select>
                      {confirmRemove === m.user_id ? (
                        <button
                          className="rounded-lg bg-red-600 px-2 py-1 text-sm font-semibold text-white"
                          onClick={() => run(() => api.removeMember(m.user_id))}
                        >
                          Remove login?
                        </button>
                      ) : (
                        <button
                          className="text-muted"
                          aria-label={`Remove ${m.display_name || m.username}`}
                          onClick={() => setConfirmRemove(m.user_id)}
                        >
                          <Trash2 className="size-4" aria-hidden />
                        </button>
                      )}
                    </>
                  ) : (
                    <span className="text-sm text-muted capitalize">{m.role}</span>
                  )}
                </li>
              ))}
            </ul>
          </section>

          {isOwner && (
            <section className="card flex flex-col gap-3" aria-labelledby="invite-title">
              <h2 id="invite-title" className="font-bold">
                Invite someone
              </h2>
              <fieldset className="flex flex-col gap-2">
                <legend className="sr-only">Role for the new person</legend>
                {ROLES.map((r) => (
                  <label key={r.value} className="flex items-start gap-3 rounded-xl border border-ink/10 p-3">
                    <input
                      type="radio"
                      name="invite-role"
                      className="mt-1 accent-leaf"
                      checked={inviteRole === r.value}
                      onChange={() => setInviteRole(r.value)}
                    />
                    <span>
                      <span className="font-semibold">{r.label}</span>
                      <span className="block text-sm text-muted">{r.hint}</span>
                    </span>
                  </label>
                ))}
              </fieldset>
              <button className="btn-secondary" onClick={invite}>
                <Link2 className="size-4" aria-hidden /> Create invite link
              </button>

              {fresh && (
                <div className="flex flex-col gap-2 rounded-xl bg-sprout/20 p-3 text-sm">
                  <p>Send this link to the person. It works once and expires in 7 days.</p>
                  <input
                    className="input text-xs select-all"
                    readOnly
                    value={inviteUrl}
                    aria-label="Invite link"
                    onFocus={(e) => e.target.select()}
                  />
                  {/* The clipboard API only works over HTTPS or localhost; on a LAN http:// install, select the text. */}
                  {window.isSecureContext && (
                    <button className="btn-secondary" onClick={() => navigator.clipboard.writeText(inviteUrl)}>
                      <Copy className="size-4" aria-hidden /> Copy link
                    </button>
                  )}
                </div>
              )}

              {invites.length > 0 && (
                <ul className="flex flex-col gap-1 text-sm" aria-label="Open invites">
                  {invites.map((i) => (
                    <li key={i.id} className="flex items-center justify-between gap-2">
                      <span>
                        <span className="capitalize">{i.role}</span> invite, expires{' '}
                        {new Date(i.expires_at).toLocaleDateString()}
                      </span>
                      <button className="text-sm text-muted underline" onClick={() => run(() => api.revokeInvite(i.id))}>
                        Cancel
                      </button>
                    </li>
                  ))}
                </ul>
              )}
            </section>
          )}
        </>
      )}
    </main>
  )
}
