import { useState } from 'react'
import { Link } from 'react-router'
import { Sprout } from 'lucide-react'
import { type Recommendation, type Recommendations as Data } from '../api'
import { t } from '../i18n'
import { useApp } from '../state'
import { Button, EmptyState, ErrorState, Section, Sheet, Skeleton } from './ui'

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

const long = (s: string) => new Date(`${s}T00:00:00`).toLocaleDateString(undefined, { day: 'numeric', month: 'short', year: 'numeric' })

/** The few things worth knowing before planting a crop here: when, how it tends to go, when it is ready, how close. */
export function KeyPoints({ r }: { r: Recommendation }) {
  const planted = r.method === 'transplant' && r.set_out_date ? r.set_out_date : r.start_date
  const rows: [string, string][] = [
    [t('When'), when(r)],
    [t('Harvest'), t('About {from} to {to}, if it goes in on {date}', { from: show(r.harvest_from), to: show(r.harvest_to), date: show(planted) })],
    [t('How it goes here'), t('Works in about {n} of 10 years in your climate', { n: Math.max(1, Math.round(r.success * 10)) })],
    [t('Spacing'), t('{n} per 30 cm cell', { n: r.plants_per_cell })],
  ]
  if (r.method === 'transplant') rows.push([t('Seedlings'), t('Sow indoors on {date}, about {weeks} weeks before setting out', { date: long(r.start_date), weeks: Math.round(r.age_days / 7) })])
  if (r.family) rows.push([t('Family'), r.where?.same_family_before ? t('{family}: grew in that spot before, so move it if you can', { family: r.family }) : r.family])
  return (
    <dl className="grid grid-cols-[auto_1fr] gap-x-4 gap-y-2 text-sm">
      {rows.map(([k, v]) => (
        <div key={k} className="contents">
          <dt className="font-semibold text-muted">{k}</dt>
          <dd>{v}</dd>
        </div>
      ))}
    </dl>
  )
}

/** A recommendation up close: its key points, a link to everything about the crop, and Plant. */
export function CropSheet({ r, onClose, onPlant }: { r: Recommendation | null; onClose: () => void; onPlant?: (q: PlantRequest) => void }) {
  return (
    <Sheet title={r?.name ?? ''} open={!!r} onClose={onClose}>
      {r && (
        <>
          <KeyPoints r={r} />
          <div className="flex flex-wrap items-center gap-2">
            {onPlant && (
              <Button
                onClick={() => {
                  onPlant(toRequest(r))
                  onClose()
                }}
              >
                {t('Plant')}
              </Button>
            )}
            <Link to={`/crops/${r.crop}`} className="btn-ghost">
              {t('Everything about {crop}', { crop: r.name })}
            </Link>
          </div>
        </>
      )}
    </Sheet>
  )
}

function List({ items, onPlant, canEdit, onOpen }: { items: Recommendation[]; onPlant: (r: PlantRequest) => void; canEdit: boolean; onOpen: (r: Recommendation) => void }) {
  return (
    <ul className="flex flex-col divide-y divide-line">
      {items.map((r) => (
        <li key={r.crop} className="flex items-center justify-between gap-3 py-3 first:pt-0 last:pb-0">
          <button type="button" className="min-w-0 flex-1 text-left" onClick={() => onOpen(r)}>
            <span className="block font-bold">{r.name}</span>
            <span className="block text-sm text-muted">
              {when(r)} · {t('harvest from {date}', { date: show(r.harvest_from) })}
            </span>
          </button>
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
  const [open, setOpen] = useState<Recommendation | null>(null)
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
          <List items={all ? data.now : data.now.slice(0, SHOWN)} onPlant={onPlant} canEdit={canEdit && !!data.has_beds} onOpen={setOpen} />
          {data.now.length > SHOWN && (
            <Button variant="ghost" onClick={() => setAll(!all)}>
              {all ? t('Show fewer') : t('Show all {count}', { count: data.now.length })}
            </Button>
          )}
        </Section>
      )}
      {data.soon.length > 0 && (
        <Section title={t('Coming up')}>
          <List items={data.soon} onPlant={onPlant} canEdit={canEdit && !!data.has_beds} onOpen={setOpen} />
        </Section>
      )}
      <CropSheet r={open} onClose={() => setOpen(null)} onPlant={canEdit && data.has_beds ? onPlant : undefined} />
    </>
  )
}
