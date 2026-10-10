import { useEffect, useState } from 'react'
import { Sprout } from 'lucide-react'
import { api, type Recommendation, type Recommendations as Data } from '../api'
import { t } from '../i18n'
import { useApp } from '../state'
import { Button, EmptyState, ErrorMessage, ErrorState, Section, Skeleton } from './ui'

const show = (s: string) => new Date(`${s}T00:00:00`).toLocaleDateString(undefined, { day: 'numeric', month: 'short' })
const SHOWN = 6

function Row({ r, canEdit, hasBeds, onPlanted }: { r: Recommendation; canEdit: boolean; hasBeds: boolean; onPlanted: () => void }) {
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState('')
  const verb = r.method === 'transplant' ? t('set out seedlings') : t('sow')
  const when =
    r.state === 'now'
      ? r.all_year
        ? t('{verb} any time', { verb })
        : t('{verb} now, until {until}', { verb, until: show(r.until) })
      : t('{verb} from {from}', { verb, from: show(r.from) })

  function plant() {
    if (!r.where) return
    setBusy(true)
    setError('')
    api
      .addPlanting({
        crop: r.crop,
        method: r.method,
        start_date: r.start_date,
        set_out_date: r.set_out_date,
        bed_id: r.where.bed_id,
        cells: r.where.cells,
        location: '',
        notes: '',
      })
      .then(onPlanted, (e) => {
        setError(e instanceof Error ? e.message : t('Failed to save'))
        setBusy(false)
      })
  }

  return (
    <li className="flex flex-col gap-1 py-3 first:pt-0 last:pb-0">
      <p>
        <span className="font-bold">{r.name}</span> <span className="text-muted">· {when}</span>
      </p>
      {r.state === 'now' && !r.all_year && r.best_from !== r.best_to && (
        <p className="text-sm text-muted">{t('Best between {a} and {b}.', { a: show(r.best_from), b: show(r.best_to) })}</p>
      )}
      {r.where ? (
        <p className="text-sm">
          {t('Room in {bed}: {cells} cells free for the whole crop, about {plants} plants.', {
            bed: r.where.bed,
            cells: r.where.free_cells,
            plants: r.where.plants,
          })}
          {r.where.same_family_before && ` ${t('The same plant family grew there before, so rotate if you can.')}`}
        </p>
      ) : (
        <p className="text-sm text-muted">{hasBeds ? t('None of your beds has room for it then.') : t('Add a bed to see where it would fit.')}</p>
      )}
      {canEdit && r.where && (
        <div>
          <Button variant="secondary" disabled={busy} onClick={plant}>
            {t('Plant in {bed}', { bed: r.where.bed })}
          </Button>
        </div>
      )}
      {error && <ErrorMessage>{error}</ErrorMessage>}
    </li>
  )
}

/** What can go in the ground now or soon at this garden, best first, and where in the plan it fits. */
export default function Recommendations({ onChange, reload }: { onChange: () => void; reload: number }) {
  const canEdit = useApp().user.role !== 'viewer'
  const [data, setData] = useState<Data | null>(null)
  const [error, setError] = useState('')
  const [all, setAll] = useState(false)

  const load = () => {
    setError('')
    api.recommendations().then(setData, (e) => setError(e instanceof Error ? e.message : t('Failed to load')))
  }
  useEffect(load, [reload]) // keeps showing the old list while the new one loads, so the page does not jump

  const title = t('What to plant')
  if (error)
    return (
      <Section title={title}>
        <ErrorState message={error} onRetry={load} />
      </Section>
    )
  if (!data) return <Skeleton className="h-40" />
  if (!data.garden) return null
  const planted = () => {
    load()
    onChange()
  }
  const now = all ? data.now : data.now.slice(0, SHOWN)
  const empty = data.now.length === 0 && data.soon.length === 0
  return (
    <Section title={title} description={t('From your climate and what each crop needs, best first.')}>
      {empty && (
        <EmptyState icon={Sprout} title={t('Nothing to start right now')}>
          {t('Nothing can go in the ground in the next three weeks. Check back as the season turns.')}
        </EmptyState>
      )}
      {data.now.length > 0 && (
        <>
          <h3 className="font-bold">{t('Plant now')}</h3>
          <ul className="flex flex-col divide-y divide-line">
            {now.map((r) => (
              <Row key={r.crop} r={r} canEdit={canEdit} hasBeds={!!data.has_beds} onPlanted={planted} />
            ))}
          </ul>
          {data.now.length > SHOWN && (
            <Button variant="ghost" onClick={() => setAll(!all)}>
              {all ? t('Show fewer') : t('Show all {count}', { count: data.now.length })}
            </Button>
          )}
        </>
      )}
      {data.soon.length > 0 && (
        <>
          <h3 className="font-bold">{t('Coming up')}</h3>
          <ul className="flex flex-col divide-y divide-line">
            {data.soon.map((r) => (
              <Row key={r.crop} r={r} canEdit={canEdit} hasBeds={!!data.has_beds} onPlanted={planted} />
            ))}
          </ul>
        </>
      )}
    </Section>
  )
}
