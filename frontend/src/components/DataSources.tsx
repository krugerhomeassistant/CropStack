import { useEffect, useState } from 'react'
import { ExternalLink } from 'lucide-react'
import { api, type DataSource, type HouseholdSettings } from '../api'
import { t } from '../i18n'
import { ErrorMessage, Section, Switch } from './ui'

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
    <Section
      title={t('Data sources')}
      description={t('Everything else stays on your server. These are the only outside services CropStack talks to.')}
    >
      {error && <ErrorMessage>{error}</ErrorMessage>}
      <ul className="-my-3 flex flex-col divide-y divide-line">
        {sources?.map((s) => (
          <li key={s.id} className="flex items-start gap-3 py-3">
            <div className="flex-1 text-sm">
              <a href={s.url} target="_blank" rel="noreferrer" className="font-semibold hover:underline">
                {s.name}
                <ExternalLink className="ml-1 inline size-3 align-baseline" aria-hidden />
              </a>
              <p className="text-muted">{t(s.used_for)}</p>
              <dl className="mt-1 grid grid-cols-[auto_1fr] gap-x-2 text-xs text-muted">
                <dt className="font-semibold">{t('Sends')}</dt>
                <dd>{t(s.sends)}</dd>
                <dt className="font-semibold">{t('When')}</dt>
                <dd>{t(s.when)}</dd>
                <dt className="font-semibold">{t('Licence')}</dt>
                <dd>{s.licence}</dd>
              </dl>
            </div>
            {s.switch ? (
              <Switch
                label={t('Use {name}', { name: s.name })}
                checked={s.enabled}
                disabled={!isOwner}
                onChange={() => toggle(s)}
              />
            ) : (
              <span className="shrink-0 text-xs text-muted">{t('Required')}</span>
            )}
          </li>
        ))}
      </ul>
      {!isOwner && <p className="text-xs text-muted">{t('Only an owner can switch sources on or off.')}</p>}
    </Section>
  )
}
