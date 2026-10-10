import { useEffect, useState } from 'react'
import { Link } from 'react-router'
import { Sprout, Trash2 } from 'lucide-react'
import { api, type Bed, type CropSummary, type Harvest, type HarvestUnit, type Planting, type PlantingStatus } from '../api'
import { N_, t } from '../i18n'
import { useApp } from '../state'
import { Badge, Button, EmptyState, ErrorState, Field, IconButton, Section, Skeleton } from './ui'

const STATUS: Record<PlantingStatus, string> = {
  planned: N_('Planned'),
  sown: N_('Sown'),
  germinated: N_('Up'),
  transplanted: N_('Set out'),
  harvesting: N_('Harvesting'),
  finished: N_('Finished'),
  failed: N_('Failed'),
}
/** The one forward step offered as a button; "failed" is a second, quieter button. Mirrors the server's rules. */
const ADVANCE: Partial<Record<PlantingStatus, (p: Planting) => PlantingStatus>> = {
  planned: () => 'sown',
  sown: () => 'germinated',
  germinated: (p) => (p.method === 'transplant' ? 'transplanted' : 'harvesting'),
  transplanted: () => 'harvesting',
  harvesting: () => 'finished',
}
const ACTION: Record<PlantingStatus, string> = {
  planned: N_('Mark sown'),
  sown: N_('Mark up'),
  germinated: N_('Mark set out'),
  transplanted: N_('Start harvest'),
  harvesting: N_('Mark finished'),
  finished: '',
  failed: '',
}

const date = (iso: string) => new Date(`${iso}T00:00:00`).toLocaleDateString(undefined, { day: 'numeric', month: 'short', year: 'numeric' })

const UNITS: Record<HarvestUnit, string> = { kg: N_('kg'), g: N_('g'), count: N_('pieces'), bunch: N_('bunches') }
const iso = (d: Date) => `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}-${String(d.getDate()).padStart(2, '0')}`

/** "2.5 kg, 12 pieces": what has been picked so far, per unit. */
function picked(rows: Harvest[]): string {
  const totals = new Map<HarvestUnit, number>()
  for (const h of rows) totals.set(h.unit, (totals.get(h.unit) ?? 0) + h.quantity)
  return [...totals].map(([unit, q]) => `${Math.round(q * 100) / 100} ${t(UNITS[unit])}`).join(', ')
}

function HarvestForm({ plantingId, onSaved }: { plantingId: number; onSaved: (h: Harvest) => void }) {
  const [open, setOpen] = useState(false)
  const [quantity, setQuantity] = useState('')
  const [unit, setUnit] = useState<HarvestUnit>('kg')
  const [error, setError] = useState('')
  if (!open)
    return (
      <Button variant="ghost" onClick={() => setOpen(true)}>
        {t('Log a harvest')}
      </Button>
    )
  return (
    <form
      className="flex flex-wrap items-end gap-2"
      onSubmit={(e) => {
        e.preventDefault()
        api
          .addHarvest(plantingId, { harvested_on: iso(new Date()), quantity: Number(quantity), unit, notes: '' })
          .then(
            (h) => {
              onSaved(h)
              setOpen(false)
              setQuantity('')
            },
            (err) => setError(err instanceof Error ? err.message : t('Failed to save')),
          )
      }}
    >
      <Field label={t('How much')} error={error}>
        <input className="input w-28" type="number" min="0" step="any" required value={quantity} onChange={(e) => setQuantity(e.target.value)} />
      </Field>
      <Field label={t('Unit')}>
        <select className="input" value={unit} onChange={(e) => setUnit(e.target.value as HarvestUnit)}>
          {(Object.keys(UNITS) as HarvestUnit[]).map((u) => (
            <option key={u} value={u}>
              {t(UNITS[u])}
            </option>
          ))}
        </select>
      </Field>
      <Button type="submit">{t('Save')}</Button>
      <Button variant="ghost" onClick={() => setOpen(false)}>
        {t('Cancel')}
      </Button>
    </form>
  )
}

/** What the household has planted or plans to plant. */
export default function Plantings({ onBedChange }: { onBedChange?: () => void }) {
  const { user } = useApp()
  const [rows, setRows] = useState<Planting[] | null>(null)
  const [harvests, setHarvests] = useState<Harvest[]>([])
  const [beds, setBeds] = useState<Bed[]>([])
  const [names, setNames] = useState<Record<string, CropSummary>>({})
  const [error, setError] = useState<string | null>(null)
  const canEdit = user.role !== 'viewer'

  function load() {
    setError(null)
    Promise.all([api.plantings(), api.crops(), api.harvests(), api.beds()]).then(
      ([plantings, crops, picks, bedRows]) => {
        setBeds(bedRows)
        setRows(plantings)
        setHarvests(picks)
        setNames(Object.fromEntries(crops.map((c) => [c.slug, c])))
      },
      (e) => setError(e instanceof Error ? e.message : t('Failed to load')),
    )
  }
  useEffect(load, [])

  const change = (id: number, body: Parameters<typeof api.updatePlanting>[1]) =>
    api.updatePlanting(id, body).then(
      (row) => setRows((rs) => rs && rs.map((r) => (r.id === id ? row : r))),
      (e) => setError(e instanceof Error ? e.message : t('Failed to save')),
    )
  const remove = (id: number) =>
    api.deletePlanting(id).then(
      () => setRows((rs) => rs && rs.filter((r) => r.id !== id)),
      (e) => setError(e instanceof Error ? e.message : t('Failed to save')),
    )

  const title = t('Plantings')
  if (error)
    return (
      <Section title={title}>
        <ErrorState message={error} onRetry={load} />
      </Section>
    )
  if (!rows) return <Skeleton className="h-32" />
  if (rows.length === 0)
    return (
      <Section title={title}>
        <EmptyState icon={Sprout} title={t('Nothing planted yet')}>
          {t('Open a crop, find when to sow it here, and choose Plant this. It shows up here.')}
        </EmptyState>
      </Section>
    )

  return (
    <Section title={title}>
      <ul className="flex flex-col divide-y divide-line">
        {rows.map((p) => {
          const next = ADVANCE[p.status]
          const crop = names[p.crop]
          const mine = harvests.filter((h) => h.planting_id === p.id)
          return (
            <li key={p.id} className="flex flex-col gap-2 py-3 first:pt-0 last:pb-0">
              <div className="flex items-start justify-between gap-3">
                <div>
                  <Link to={`/crops/${p.crop}`} className="font-bold underline-offset-2 hover:underline">
                    {crop?.names.en?.[0] ?? p.crop}
                  </Link>
                  <p className="text-sm text-muted">
                    {t('{count} planted', { count: p.quantity })}
                    {p.location && ` · ${p.location}`}
                  </p>
                  {mine.length > 0 && <p className="text-sm font-semibold text-leaf">{t('Picked: {total}', { total: picked(mine) })}</p>}
                  <p className="text-sm text-muted">
                    {p.method === 'transplant'
                      ? t('Sow indoors {sow}, set out {out}', { sow: date(p.start_date), out: date(p.set_out_date ?? p.start_date) })
                      : t('Sow {sow}', { sow: date(p.start_date) })}
                  </p>
                </div>
                <Badge tone={p.status === 'failed' ? 'marigold' : p.status === 'planned' ? 'muted' : 'leaf'}>{t(STATUS[p.status])}</Badge>
              </div>
              {canEdit && (
                <div className="flex flex-wrap items-center gap-2">
                  {next && (
                    <Button variant="secondary" onClick={() => change(p.id, { status: next(p) })}>
                      {t(ACTION[p.status])}
                    </Button>
                  )}
                  {next && (
                    <Button variant="ghost" onClick={() => change(p.id, { status: 'failed' })}>
                      {t('It failed')}
                    </Button>
                  )}
                  {!['planned', 'sown', 'failed'].includes(p.status) && (
                    <HarvestForm plantingId={p.id} onSaved={(h) => setHarvests((hs) => [...hs, h])} />
                  )}
                  {beds.length > 0 && (
                    <select
                      className="input w-auto"
                      aria-label={t('Bed for {crop}', { crop: crop?.names.en?.[0] ?? p.crop })}
                      value={p.bed_id ?? ''}
                      onChange={(e) => change(p.id, { bed_id: e.target.value ? Number(e.target.value) : null }).then(onBedChange)}
                    >
                      <option value="">{t('No bed')}</option>
                      {beds.map((b) => (
                        <option key={b.id} value={b.id}>
                          {b.name}
                        </option>
                      ))}
                    </select>
                  )}
                  <IconButton icon={Trash2} label={t('Delete planting')} onClick={() => remove(p.id)} />
                </div>
              )}
            </li>
          )
        })}
      </ul>
    </Section>
  )
}
