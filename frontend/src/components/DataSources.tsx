import { useEffect, useState } from 'react'
import { ExternalLink } from 'lucide-react'
import { api, type DataSource, type HouseholdSettings } from '../api'
import { t } from '../i18n'

/** Settings → Data sources: every outside service, what is sent and when (SPEC P7). Owners switch the optional ones. */
export default function DataSources({ isOwner }: { isOwner: boolean }) {
  const [sources, setSources] = useState<DataSource[] | null>(null)
  const [error, setError] = useState('')

  const load = () => api.dataSources().then(setSources, (e) => setError(e instanceof Error ? e.message : t('Failed to load')))
  useEffect(() => {
    load()
  }, [])

  async function toggle(source: DataSource) {
    if (!sources || !source.switch) return
    const settings = Object.fromEntries(
      sources.filter((s) => s.switch).map((s) => [s.switch, s.id === source.id ? !s.enabled : s.enabled]),
    ) as HouseholdSettings
    setSources(sources.map((s) => (s.id === source.id ? { ...s, enabled: !s.enabled } : s))) // optimistic
    try {
      await api.saveHouseholdSettings(settings)
    } catch (e) {
      setError(e instanceof Error ? e.message : t('Something went wrong'))
      load()
    }
  }

  return (
    <section className="card flex flex-col gap-3" aria-labelledby="sources-title">
      <h2 id="sources-title" className="font-bold">
        {t('Data sources')}
      </h2>
      <p className="text-sm text-muted">
        {t('Everything else stays on your server. These are the only outside services CropStack talks to.')}
      </p>
      {error && (
        <p className="text-sm text-red-600" role="alert">
          {error}
        </p>
      )}
      <ul className="flex flex-col divide-y divide-ink/10">
        {sources?.map((s) => (
          <li key={s.id} className="flex items-start gap-3 py-3">
            <div className="flex-1 text-sm">
              <a href={s.url} target="_blank" rel="noreferrer" className="font-semibold hover:underline">
                {s.name}
                <ExternalLink className="ml-1 inline size-3 align-baseline" aria-hidden />
              </a>
              <p className="text-muted">{t(s.used_for)}</p>
              <p className="text-xs text-muted">
                {t('Sends: {what} · {when} · {licence}', { what: t(s.sends), when: t(s.when), licence: s.licence })}
              </p>
            </div>
            {s.switch ? (
              <label className="flex shrink-0 items-center gap-2 text-sm">
                <span className="sr-only">{t('Use {name}', { name: s.name })}</span>
                <input
                  type="checkbox"
                  role="switch"
                  className="switch"
                  checked={s.enabled}
                  disabled={!isOwner}
                  onChange={() => toggle(s)}
                />
              </label>
            ) : (
              <span className="shrink-0 text-xs text-muted">{t('Required')}</span>
            )}
          </li>
        ))}
      </ul>
      {!isOwner && <p className="text-xs text-muted">{t('Only an owner can switch sources on or off.')}</p>}
    </section>
  )
}
