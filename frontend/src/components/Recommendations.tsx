import { useState } from 'react'
import { Sprout } from 'lucide-react'
import { type Recommendation, type Recommendations as Data } from '../api'
import { t } from '../i18n'
import { useApp } from '../state'
import { Button, EmptyState, ErrorState, Section, Skeleton } from './ui'

const show = (s: string) => new Date(`${s}T00:00:00`).toLocaleDateString(undefined, { day: 'numeric', month: 'short' })
const SHOWN = 8

/** What to do with a recommendation: take it to the bed grid with the crop already chosen. */
export type PlantRequest = { crop: string; method: 'direct' | 'transplant'; weeks: number; date: string; bedId: number | null }
export const toRequest = (r: Recommendation): PlantRequest => ({
  crop: r.crop,
  method: r.method,
  weeks: Math.max(1, Math.round(r.age_days / 7)),
  date: r.method === 'transplant' && r.set_out_date ? r.set_out_date : r.start_date,
  bedId: r.where?.bed_id ?? null,
})

function when(r: Recommendation): string {
  const verb = r.method === 'transplant' ? t('Set out') : t('Sow')
  if (r.state === 'soon') return t('{verb} from {from}', { verb, from: show(r.from) })
  if (r.all_year) return t('{verb} any time', { verb })
  return r.best_from !== r.best_to ? t('{verb} now · best {a} to {b}', { verb, a: show(r.best_from), b: show(r.best_to) }) : t('{verb} now', { verb })
}

function List({ items, onPlant, canEdit }: { items: Recommendation[]; onPlant: (r: PlantRequest) => void; canEdit: boolean }) {
  return (
    <ul className="flex flex-col divide-y divide-line">
      {items.map((r) => (
        <li key={r.crop} className="flex items-center justify-between gap-3 py-3 first:pt-0 last:pb-0">
          <div className="min-w-0">
            <p className="font-bold">{r.name}</p>
            <p className="text-sm text-muted">{when(r)}</p>
          </div>
          {canEdit && (
            <Button variant="secondary" onClick={() => onPlant(toRequest(r))}>
              {t('Plant')}
            </Button>
          )}
        </li>
      ))}
    </ul>
  )
}

/** The Plant tab: what can go in the ground now or soon here, best first. One tap takes you to a bed to place it. */
export default function Recommendations({ data, error, retry, onPlant }: { data: Data | null; error: string; retry: () => void; onPlant: (r: PlantRequest) => void }) {
  const canEdit = useApp().user.role !== 'viewer'
  const [all, setAll] = useState(false)
  if (error) return <ErrorState message={error} onRetry={retry} />
  if (!data) return <Skeleton className="h-40" />
  if (!data.garden) return null
  if (data.now.length === 0 && data.soon.length === 0)
    return (
      <Section>
        <EmptyState icon={Sprout} title={t('Nothing to start right now')}>
          {t('Nothing can go in the ground in the next three weeks. Check back as the season turns.')}
        </EmptyState>
      </Section>
    )
  return (
    <>
      {!data.has_beds && canEdit && <p className="rounded-[var(--radius-row)] bg-sunken p-3 text-sm">{t('Draw a bed on the Plan tab first, then come back and plant into it.')}</p>}
      {data.now.length > 0 && (
        <Section title={t('Plant now')}>
          <List items={all ? data.now : data.now.slice(0, SHOWN)} onPlant={onPlant} canEdit={canEdit && !!data.has_beds} />
          {data.now.length > SHOWN && (
            <Button variant="ghost" onClick={() => setAll(!all)}>
              {all ? t('Show fewer') : t('Show all {count}', { count: data.now.length })}
            </Button>
          )}
        </Section>
      )}
      {data.soon.length > 0 && (
        <Section title={t('Coming up')}>
          <List items={data.soon} onPlant={onPlant} canEdit={canEdit && !!data.has_beds} />
        </Section>
      )}
    </>
  )
}
