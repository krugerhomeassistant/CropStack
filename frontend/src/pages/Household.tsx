import { useEffect, useState, type FormEvent } from 'react'
import { Copy, Link2, Trash2 } from 'lucide-react'
import { api, type Household as HouseholdData, type NewInvite, type PendingInvite, type Role } from '../api'
import { N_, t } from '../i18n'
import { Button, ErrorMessage, IconButton, PageHeader, RadioCards, Section } from '../components/ui'
import { useApp } from '../state'

const ROLES: { value: Role; label: string; hint: string }[] = [
  { value: 'member', label: N_('Member'), hint: N_('Sees and does the daily tasks, logs harvests and notes') },
  { value: 'viewer', label: N_('Viewer'), hint: N_('Can look, but not change anything') },
  { value: 'owner', label: N_('Owner'), hint: N_('Everything, including the garden location and members') },
]

export default function Household() {
  const { user } = useApp()
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
      setError(err instanceof Error ? err.message : t('Failed to load'))
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
      setError(err instanceof Error ? err.message : t('Something went wrong'))
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
    <>
      <PageHeader back title={t('Household')} subtitle={t('Everyone who shares this garden, and what they can do.')} />

      {error && <ErrorMessage>{error}</ErrorMessage>}

      {data && (
        <>
          <form className="card flex flex-col gap-3" onSubmit={rename}>
            <label className="field">
              <span>{t('Household name')}</span>
              <input
                className="input"
                value={name}
                maxLength={80}
                required
                disabled={!isOwner}
                onChange={(e) => setName(e.target.value)}
              />
            </label>
            {isOwner && name.trim() !== data.name && (
              <Button type="submit" className="self-start">
                {t('Save name')}
              </Button>
            )}
          </form>

          <Section title={t('People')}>
            <ul className="-my-2 flex flex-col divide-y divide-line">
              {data.members.map((m) => (
                <li key={m.user_id} className="flex flex-wrap items-center gap-2 py-2">
                  <span className="min-w-0 flex-1">
                    <span className="font-semibold">{m.display_name || m.username}</span>
                    {m.user_id === user.id && <span className="text-sm text-muted"> {t('(you)')}</span>}
                    <span className="block text-xs text-muted">@{m.username}</span>
                  </span>
                  {isOwner && m.user_id !== user.id ? (
                    <>
                      <label className="sr-only" htmlFor={`role-${m.user_id}`}>
                        {t('Role for {name}', { name: m.display_name || m.username })}
                      </label>
                      <select
                        id={`role-${m.user_id}`}
                        className="input w-auto text-sm"
                        value={m.role}
                        onChange={(e) => run(() => api.setRole(m.user_id, e.target.value as Role))}
                      >
                        {ROLES.map((r) => (
                          <option key={r.value} value={r.value}>
                            {t(r.label)}
                          </option>
                        ))}
                      </select>
                      {confirmRemove === m.user_id ? (
                        <Button variant="danger" onClick={() => run(() => api.removeMember(m.user_id))}>
                          {t('Remove login?')}
                        </Button>
                      ) : (
                        <IconButton
                          icon={Trash2}
                          label={t('Remove {name}', { name: m.display_name || m.username })}
                          onClick={() => setConfirmRemove(m.user_id)}
                        />
                      )}
                    </>
                  ) : (
                    <span className="text-sm text-muted">{t(ROLES.find((r) => r.value === m.role)?.label ?? m.role)}</span>
                  )}
                </li>
              ))}
            </ul>
          </Section>

          {isOwner && (
            <Section title={t('Invite someone')} description={t('Choose what the new person can do, then send them the link.')}>
              <RadioCards
                legend={t('Role for the new person')}
                hideLegend
                name="invite-role"
                options={ROLES.map((r) => ({ ...r, label: t(r.label), hint: t(r.hint) }))}
                value={inviteRole}
                onChange={setInviteRole}
              />
              <Button variant="secondary" className="self-start" onClick={invite}>
                <Link2 className="size-4" aria-hidden /> {t('Create invite link')}
              </Button>

              {fresh && (
                <div className="flex flex-col gap-2 rounded-[var(--radius-row)] bg-sunken p-3 text-sm">
                  <p>{t('Send this link to the person. It works once and expires in 7 days.')}</p>
                  <input
                    className="input text-xs select-all"
                    readOnly
                    value={inviteUrl}
                    aria-label={t('Invite link')}
                    onFocus={(e) => e.target.select()}
                  />
                  {/* The clipboard API only works over HTTPS or localhost; on a LAN http:// install, select the text. */}
                  {window.isSecureContext && (
                    <Button variant="secondary" className="self-start" onClick={() => navigator.clipboard.writeText(inviteUrl)}>
                      <Copy className="size-4" aria-hidden /> {t('Copy link')}
                    </Button>
                  )}
                </div>
              )}

              {invites.length > 0 && (
                <ul className="flex flex-col gap-1 text-sm" aria-label={t('Open invites')}>
                  {invites.map((i) => (
                    <li key={i.id} className="flex items-center justify-between gap-2">
                      <span>
                        {t('{role} invite, expires {date}', {
                          role: t(ROLES.find((r) => r.value === i.role)?.label ?? i.role),
                          date: new Date(i.expires_at).toLocaleDateString(),
                        })}
                      </span>
                      <Button variant="ghost" onClick={() => run(() => api.revokeInvite(i.id))}>
                        {t('Cancel')}
                      </Button>
                    </li>
                  ))}
                </ul>
              )}
            </Section>
          )}
        </>
      )}
    </>
  )
}
