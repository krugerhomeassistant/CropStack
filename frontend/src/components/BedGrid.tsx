import ArrangePanel, { type Area, type Ghost } from './ArrangePanel'
import StatusSelect from './StatusSelect'
import { useEffect, useRef, useState } from 'react'
import { Eraser } from 'lucide-react'
import { api, type Bed, type CropSummary, type Placement, type PlanItem, type Recommendation } from '../api'
import { t } from '../i18n'
import { useApp } from '../state'
import { CropSheet, toRequest, type PlantRequest } from './Recommendations'
import { CropIcon, cropIconUrl } from './CropIcon'
import { Button, ErrorMessage, Field } from './ui'
import DateField from './ui/DateField'

export const iso = (d: Date) => `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}-${String(d.getDate()).padStart(2, '0')}`
export const addDays = (s: string, n: number) => iso(new Date(new Date(`${s}T00:00:00`).getTime() + n * 864e5))
const key = (c: number, r: number) => `${c},${r}`
const show = (s: string) => new Date(`${s}T00:00:00`).toLocaleDateString(undefined, { day: 'numeric', month: 'short', year: 'numeric' })

/** A steady colour for each crop, so the same crop looks the same everywhere. */
export function cropColour(slug: string): string {
  let h = HUES[slug]
  if (h === undefined) {
    h = 0
    for (const ch of slug) h = (h * 31 + ch.charCodeAt(0)) % 360
  }
  return `hsl(${h} 55% 55% / 0.5)`
}
// Crops whose colour everyone knows keep it; the rest get a steady hue from their name.
const HUES: Record<string, number> = {
  beetroot: 350, radish: 335, strawberry: 355, tomato: 8, chilli: 18, carrot: 30, pumpkin: 34, 'sweet-potato': 24, potato: 42, onion: 40,
  'sweet-corn': 52, lettuce: 105, cabbage: 95, kale: 140, spinach: 130, broccoli: 150, cucumber: 118, zucchini: 135, 'green-bean': 100, pea: 85, eggplant: 285,
}

/** What is in a bed (or the whole garden) on a date: plants per crop. */
export function PlantedSummary({ beds, on }: { beds: Bed[]; on: string }) {
  const sums = new Map<string, { name: string; now: number }>()
  for (const b of beds)
    for (const p of b.placements) {
      if (p.from > on || p.until < on) continue
      const shown = p.spots.filter(([x, y]) => x < b.width * 100 && y < b.length * 100).length // only what the bed shows
      const inside = p.cells.filter(([c, r]) => c < b.cols && r < b.rows).length
      if (shown === 0 && (p.spots.length > 0 || inside === 0)) continue
      const s = sums.get(p.crop) ?? { name: p.name, now: 0 }
      s.now += p.spots.length ? shown : Math.round((p.quantity * inside) / p.cells.length)
      sums.set(p.crop, s)
    }
  if (sums.size === 0) return <p className="text-sm text-muted">{t('Nothing is planted on this date.')}</p>
  return (
    <ul className="flex flex-col gap-0.5 text-sm" aria-label={t('What is planted')}>
      {[...sums].map(([crop, s]) => (
        <li key={crop} className="flex items-center gap-2">
          <span aria-hidden><CropIcon crop={crop} /></span>
          <span className="font-semibold">{s.now}× {s.name}</span>
        </li>
      ))}
    </ul>
  )
}

/** What is in one bed on the chosen date, each planting with its stage to change. One that stands nowhere on the grid
 *  (made before plants had places) is listed too, with a button that finds it room. */
function BedPlantings({ bed, on, canEdit, onChange, fail }: { bed: Bed; on: string; canEdit: boolean; onChange: () => void; fail: (e: unknown) => void }) {
  const live = (p: Placement) => !['finished', 'failed'].includes(p.status)
  const rows = bed.placements.filter((p) => (p.from <= on && on <= p.until) || (live(p) && p.spots.length === 0))
  if (rows.length === 0) return <p className="text-sm text-muted">{t('Nothing is planted on this date.')}</p>
  return (
    <ul className="flex flex-col gap-2 text-sm" aria-label={t('What is planted')}>
      {rows.map((p) => (
        <li key={p.planting_id} className="flex flex-wrap items-center justify-between gap-2">
          <span className="flex items-center gap-2 font-semibold">
            <span aria-hidden><CropIcon crop={p.crop} /></span>
            {p.quantity}× {p.name}
          </span>
          {canEdit && (
            <span className="flex items-center gap-2">
              {p.spots.length === 0 && live(p) && (
                <Button variant="secondary" onClick={() => api.placePlanting(p.planting_id).then(onChange, fail)}>
                  {t('Place in bed')}
                </Button>
              )}
              <StatusSelect status={p.status} method={p.method} label={t('Stage of {crop}', { crop: p.name })} onChange={(status) => api.updatePlanting(p.planting_id, { status }).then(onChange, fail)} />
            </span>
          )}
          {p.spots.length === 0 && live(p) && <span className="-mt-1 w-full pl-7 text-muted">{t('Not on the grid yet.')}</span>}
        </li>
      ))}
    </ul>
  )
}

type Brush = { crop: string; method: 'direct' | 'transplant'; weeks: number } | 'erase' | null
const SUGGESTED = 6

/** The inside of one bed, cell by cell, on any date. Choose a crop and drag across cells to plant it from that date;
 *  the same cell can hold something else before or after, so a bed can be mixed and staggered. */
export default function BedGrid({
  bed,
  crops,
  suggested,
  request,
  plan,
  on,
  onChange,
}: {
  bed: Bed
  crops: CropSummary[]
  suggested: Recommendation[]
  request: PlantRequest | null
  plan: PlanItem[]
  on: string // the date being looked at, chosen above the plan
  onChange: () => void
}) {
  const canEdit = useApp().user.role !== 'viewer'
  const today = iso(new Date())
  const [brush, setBrush] = useState<Brush>(request ? { crop: request.crop, method: request.method, weeks: request.weeks } : null)
  const [painted, setPainted] = useState<string[]>([])
  const strokeRef = useRef<string[]>([]) // the cells of the stroke so far; a quick tap can end before a re-render
  const [info, setInfo] = useState<Placement | null>(null)
  const [editing, setEditing] = useState(false)
  const [until, setUntil] = useState('')
  const [sow, setSow] = useState('')
  const [setOut, setSetOut] = useState('')
  const [qty, setQty] = useState('')
  const [error, setError] = useState('')
  const [about, setAbout] = useState<Recommendation | null>(null)
  const [arranged, setArranged] = useState<Ghost[]>([]) // an Arrange preview, shown whatever the date
  const [arranging, setArranging] = useState(false)
  const [area, setArea] = useState<Area>(null) // the section drawn for Arrange
  const dragFrom = useRef<[number, number] | null>(null)

  // arriving from a recommendation: the crop is chosen and the date set
  useEffect(() => {
    if (!request) return
    setBrush({ crop: request.crop, method: request.method, weeks: request.weeks })
  }, [request])

  const here = (c: number, r: number) =>
    bed.placements.filter((p) => p.cells.some(([x, y]) => x === c && y === r) && p.from <= on && on <= p.until)
  // the drafted year plan, its plants shown dashed on this date
  const ghosts: Ghost[] = [...plan.filter((i) => i.bed_id === bed.id && (i.set_out_date ?? i.start_date) <= on && on <= i.until), ...arranged]
  const clashing = new Set(bed.clashes.flatMap((x) => x.plantings))
  const fail = (e: unknown) => setError(e instanceof Error ? e.message : t('Failed to save'))

  const at = (e: React.PointerEvent<SVGSVGElement>) => {
    const box = e.currentTarget.getBoundingClientRect()
    const c = Math.floor(((e.clientX - box.left) / box.width) * bed.cols)
    const r = Math.floor(((e.clientY - box.top) / box.height) * bed.rows)
    return c >= 0 && r >= 0 && c < bed.cols && r < bed.rows ? key(c, r) : null
  }
  // the plant standing under a tap, else whatever holds the cell
  const plantAt = (e: React.PointerEvent<SVGSVGElement>, c: number, r: number) => {
    const box = e.currentTarget.getBoundingClientRect()
    const x = ((e.clientX - box.left) / box.width) * bed.cols * bed.cell_cm
    const y = ((e.clientY - box.top) / box.height) * bed.rows * bed.cell_cm
    return (
      bed.placements.find((p) => p.from <= on && on <= p.until && p.spots.some(([sx, sy, w, h]) => x >= sx && x < sx + w && y >= sy && y < sy + h)) ??
      here(c, r)[0] ??
      null
    )
  }
  function add(e: React.PointerEvent<SVGSVGElement>) {
    const k = at(e)
    if (k && !strokeRef.current.includes(k)) {
      strokeRef.current = [...strokeRef.current, k]
      setPainted(strokeRef.current)
    }
  }
  function drawTo(k: string | null) {
    const from = dragFrom.current
    if (!from || !k) return
    const [c, r] = k.split(',').map(Number)
    setArea([Math.min(from[0], c), Math.min(from[1], r), Math.max(from[0], c), Math.max(from[1], r)])
  }
  function down(e: React.PointerEvent<SVGSVGElement>) {
    setError('')
    e.currentTarget.setPointerCapture(e.pointerId)
    if (arranging) {
      const k = at(e)
      dragFrom.current = k ? (k.split(',').map(Number) as [number, number]) : null
      return drawTo(k)
    }
    if (brush && canEdit) return add(e)
    const k = at(e)
    const [c, r] = k ? k.split(',').map(Number) : [-1, -1]
    const p = plantAt(e, c, r)
    setInfo(p)
    setEditing(false)
    setUntil(p?.until ?? '')
    setSow(p?.start_date ?? '')
    setSetOut(p?.set_out_date ?? '')
    setQty(p ? String(p.quantity) : '')
  }
  function up() {
    dragFrom.current = null
    const cells = strokeRef.current.map((k) => k.split(',').map(Number) as [number, number])
    strokeRef.current = []
    setPainted([])
    if (!brush || cells.length === 0) return
    if (brush === 'erase') {
      const byPlanting = new Map<number, [number, number][]>()
      for (const [c, r] of cells) for (const p of here(c, r)) byPlanting.set(p.planting_id, [...(byPlanting.get(p.planting_id) ?? []), [c, r]])
      Promise.all(
        [...byPlanting].map(([id, gone]) => {
          const mine = bed.placements.find((p) => p.planting_id === id)!
          return api.updatePlanting(id, { cells: mine.cells.filter(([x, y]) => !gone.some(([a, b]) => a === x && b === y)) })
        }),
      ).then(onChange, fail)
      return
    }
    const transplant = brush.method === 'transplant'
    const start = transplant ? addDays(on, -7 * brush.weeks) : on
    // Painting more of the same crop on the same day grows that planting instead of adding another row.
    const same = bed.placements.find(
      (p) => p.crop === brush.crop && p.method === brush.method && p.start_date === start && !['finished', 'failed'].includes(p.status),
    )
    if (same) {
      const union = [...same.cells, ...cells.filter(([c, r]) => !same.cells.some(([x, y]) => x === c && y === r))]
      if (union.length === same.cells.length) return
      api
        .updatePlanting(same.planting_id, {
          cells: union, // the server keeps the plants already there and adds new ones only on the new cells
        })
        .then(onChange, fail)
      return
    }
    api
      .addPlanting({
        crop: brush.crop,
        method: brush.method,
        start_date: start,
        set_out_date: transplant ? on : null,
        bed_id: bed.id,
        cells,
        in_ground: on <= today, // painted on today or earlier: it is already in the ground
        location: '',
        notes: '',
      })
      .then(onChange, fail)
  }

  const crop = brush && brush !== 'erase' ? brush : null
  const chips = suggested.slice(0, SUGGESTED)
  const nameOf = (slug: string) => crops.find((c) => c.slug === slug)?.names.en?.[0] ?? slug
  const pick = (r: Recommendation) => {
    const q = toRequest(r)
    setBrush(crop?.crop === r.crop ? null : { crop: q.crop, method: q.method, weeks: q.weeks })
  }

  return (
    <div className="flex flex-col gap-4">
      {canEdit && on < today && (
        <p className="text-sm text-muted">{t('Already growing? Plant on the day it went in and it is recorded as sown (or set out), with its harvest worked out from then.')}</p>
      )}

      {canEdit && (
        <div className="flex flex-col gap-2">
          {chips.length > 0 && (
            <p className="text-sm">
              <span className="font-semibold">{t('Good to plant now')}</span>{' '}
              <span className="text-muted">{t('in your climate, best first')}</span>
            </p>
          )}
          <div className="-mx-1 flex gap-2 overflow-x-auto px-1 pb-1" role="group" aria-label={t('Choose what to plant')}>
            {chips.map((r) => (
              <button
                key={r.crop}
                type="button"
                aria-pressed={crop?.crop === r.crop}
                onClick={() => pick(r)}
                className={`flex min-h-16 min-w-20 shrink-0 flex-col items-center justify-center gap-0.5 rounded-xl border-2 px-3 py-2 text-sm font-semibold ${crop?.crop === r.crop ? 'border-leaf bg-leaf/15' : 'border-line bg-surface'}`}
              >
                <span className="text-2xl leading-none" aria-hidden>
                  <CropIcon crop={r.crop} />
                </span>
                {r.name}
              </button>
            ))}
            <button
              type="button"
              aria-pressed={brush === 'erase'}
              onClick={() => setBrush(brush === 'erase' ? null : 'erase')}
              className={`flex min-h-16 min-w-20 shrink-0 flex-col items-center justify-center gap-1 rounded-xl border-2 px-3 py-2 text-sm font-semibold ${brush === 'erase' ? 'border-leaf bg-leaf/15' : 'border-line bg-surface'}`}
            >
              <Eraser className="size-6" aria-hidden />
              {t('Take out of cells')}
            </button>
          </div>
          <div className="flex flex-wrap items-end gap-2">
            <Field label={t('Plant')}>
              <select
                className="input"
                value={crop && !chips.some((r) => r.crop === crop.crop) ? crop.crop : ''}
                onChange={(e) => e.target.value && setBrush({ crop: e.target.value, method: crop?.method ?? 'direct', weeks: crop?.weeks ?? 5 })}
              >
                <option value="">{crop && chips.some((r) => r.crop === crop.crop) ? nameOf(crop.crop) : t('Another crop…')}</option>
                {crops.map((c) => (
                  <option key={c.slug} value={c.slug}>
                    {c.names.en?.[0] ?? c.slug}
                  </option>
                ))}
              </select>
            </Field>
            {crop && (
              <>
                <Field label={t('How')}>
                  <select className="input" value={crop.method} onChange={(e) => setBrush({ ...crop, method: e.target.value as 'direct' | 'transplant' })}>
                    <option value="direct">{t('Sow seeds')}</option>
                    <option value="transplant">{t('Set out seedlings')}</option>
                  </select>
                </Field>
                {crop.method === 'transplant' && (
                  <Field label={t('Weeks indoors')}>
                    <input className="input w-20" type="number" min={1} max={20} value={crop.weeks} onChange={(e) => setBrush({ ...crop, weeks: Number(e.target.value) || 1 })} />
                  </Field>
                )}
              </>
            )}
          </div>
        </div>
      )}
      {crop && suggested.some((r) => r.crop === crop.crop) && (() => {
        const r = suggested.find((x) => x.crop === crop.crop)!
        return (
          <div className="flex items-center justify-between gap-3 rounded-[var(--radius-row)] bg-sunken p-3 text-sm">
            <span>
              {r.purpose === 'companion' ? t('Flowers from about {date}', { date: show(r.harvest_from) }) : t('Harvest from about {date}', { date: show(r.harvest_from) })} · {r.cells_per_plant > 1 ? t('1 plant per {n} cells', { n: r.cells_per_plant }) : t('{n} per cell', { n: r.plants_per_cell })}
            </span>
            <Button variant="ghost" onClick={() => setAbout(r)}>
              {t('Key points')}
            </Button>
          </div>
        )
      })()}
      <CropSheet r={about} onClose={() => setAbout(null)} />
      <p className="text-sm text-muted">
        {crop
          ? t('Drag across the cells to plant {crop} from {date}.', { crop: nameOf(crop.crop), date: show(on) })
          : brush === 'erase'
            ? t('Drag across cells to take what is growing there on {date} out of them.', { date: show(on) })
            : canEdit
              ? t('Choose a crop, then drag across the cells. Tap a cell to see what is in it.')
              : t('Tap a cell to see what is in it.')}
      </p>

      <div className="mx-auto w-full rounded-2xl border border-line bg-sunken p-1.5" style={{ maxWidth: `${bed.cols * 4.5}rem` }}>
      <svg
        viewBox={`0 0 ${bed.cols} ${bed.rows}`}
        className="block w-full touch-none select-none"
        role="img"
        aria-label={t('Cells of {bed}', { bed: bed.name })}
        onPointerDown={down}
        onPointerMove={(e) => (dragFrom.current ? drawTo(at(e)) : brush && canEdit && e.buttons && add(e))}
        onPointerUp={up}
      >
        {Array.from({ length: bed.rows }, (_, r) =>
          Array.from({ length: bed.cols }, (_, c) => {
            const marked = painted.includes(key(c, r))
            return (
              <g key={key(c, r)}>
                <rect
                  x={c + 0.03}
                  y={r + 0.03}
                  width={0.94}
                  height={0.94}
                  rx={0.14}
                  fill={marked && crop ? cropColour(crop.crop) : 'transparent'}
                  className={marked ? 'stroke-ink' : 'stroke-line'}
                  strokeWidth={marked ? 0.06 : 0.025}
                  strokeDasharray={marked ? '0.15 0.1' : undefined}
                />
              </g>
            )
          }),
        )}
        {area && (
          <rect x={area[0]} y={area[1]} width={area[2] - area[0] + 1} height={area[3] - area[1] + 1} rx={0.14} fill="none" className="pointer-events-none stroke-leaf" strokeWidth={0.1} strokeDasharray="0.25 0.15" />
        )}
        {ghosts.flatMap((i) =>
          i.spots.map(([sx, sy, w, h], n) => {
            const u = bed.cell_cm
            const side = Math.min(w, h) / u
            return (
              <g key={`plan-${i.crop}-${n}`} className="pointer-events-none" opacity={0.6}>
                <rect x={sx / u + 0.02} y={sy / u + 0.02} width={w / u - 0.04} height={h / u - 0.04} rx={Math.min(0.14, side / 4)} fill={cropColour(i.crop)} fillOpacity={0.5} className="stroke-ink" strokeWidth={0.03} strokeDasharray="0.12 0.08" />
                <image href={cropIconUrl(i.crop)} x={sx / u + (w / u - side * 0.6) / 2} y={sy / u + (h / u - side * 0.6) / 2} width={side * 0.6} height={side * 0.6} />
              </g>
            )
          }),
        )}
        {/* the plants themselves: each one a square of its own real spacing, whatever the cells are */}
        {bed.placements
          .filter((p) => p.from <= on && on <= p.until)
          .flatMap((p) =>
            p.spots.map(([sx, sy, w, h], i) => {
              const u = bed.cell_cm
              const side = Math.min(w, h) / u
              return (
                <g key={`${p.planting_id}-${i}`} className="pointer-events-none">
                  <rect
                    x={sx / u + 0.02}
                    y={sy / u + 0.02}
                    width={w / u - 0.04}
                    height={h / u - 0.04}
                    rx={Math.min(0.14, side / 4)}
                    fill={cropColour(p.crop)}
                    className={clashing.has(p.planting_id) ? 'stroke-danger' : 'stroke-ink/40'}
                    strokeWidth={clashing.has(p.planting_id) ? 0.06 : 0.02}
                  />
                  <image href={cropIconUrl(p.crop)} x={sx / u + (w / u - side * 0.6) / 2} y={sy / u + (h / u - side * 0.6) / 2 - (side > 0.9 ? 0.08 : 0)} width={side * 0.6} height={side * 0.6} />
                  {side > 0.9 && (
                    <text x={sx / u + w / u / 2} y={sy / u + h / u - 0.1} fontSize={0.18} textAnchor="middle" className="fill-ink">
                      {p.name.slice(0, 8)}
                    </text>
                  )}
                </g>
              )
            }),
          )}
      </svg>
      </div>
      <p className="text-xs text-muted">
        {t('One cell is {size} cm square.', { size: bed.cell_cm })}
        {plan.length > 0 && ` ${t('Dashed plants are the drafted plan; step the date to see it through the year.')}`}
        {bed.outside > 0 && ` ${t('{n} planted cells sit beyond the edge of this bed; make the bed bigger to see them.', { n: bed.outside })}`}
      </p>
      {canEdit && bed.clashes.length > 0 && (
        <Button
          variant="secondary"
          onClick={async () => {
            try {
              for (const id of new Set(bed.clashes.map((x) => Math.max(...x.plantings)))) await api.placePlanting(id) // the newer one moves
              onChange()
            } catch (e) {
              fail(e)
            }
          }}
        >
          {t('Fix overlaps')}
        </Button>
      )}
      <BedPlantings bed={bed} on={on} canEdit={canEdit} onChange={onChange} fail={fail} />
      {canEdit && <ArrangePanel bed={bed} crops={crops} on={on} area={area} onArea={setArea} onOpen={setArranging} onPreview={setArranged} onChange={onChange} />}

      {info && (
        <div className="flex flex-col gap-2 rounded-[var(--radius-row)] bg-sunken p-3 text-sm">
          <div className="flex items-start justify-between gap-3">
            <div>
              <p className="font-bold">{info.name}</p>
              <p className="text-muted">
                {t('{count} plants · {from} to {until}', { count: info.quantity, from: show(info.from), until: show(info.until) })}
              </p>
              {info.harvest_from && info.harvest_to && (
                <p>{info.purpose === 'companion' ? t('Flowering expected {from} to {to}', { from: show(info.harvest_from), to: show(info.harvest_to) }) : t('Harvest expected {from} to {to}', { from: show(info.harvest_from), to: show(info.harvest_to) })}</p>
              )}
              {info.next_job && <p>{t('Next: {job}, {date}', { job: info.next_job.title, date: show(info.next_job.date) })}</p>}
            </div>
            {canEdit && (
              <Button variant="ghost" onClick={() => setEditing(!editing)}>
                {editing ? t('Close') : t('Edit')}
              </Button>
            )}
          </div>
          {canEdit && editing && (
            <form
              className="flex flex-wrap items-end gap-2"
              onSubmit={(e) => {
                e.preventDefault()
                setError('')
                api
                  .updatePlanting(info.planting_id, {
                    start_date: sow,
                    set_out_date: info.method === 'transplant' ? setOut : null,
                    quantity: Number(qty),
                    ends_on: until || null,
                  })
                  .then(() => {
                    setInfo(null)
                    onChange()
                  }, fail)
              }}
            >
              <Field label={t('Sow date')}>
                <DateField required value={sow} onChange={setSow} />
              </Field>
              {info.method === 'transplant' && (
                <Field label={t('Set-out date')}>
                  <DateField required value={setOut} onChange={setSetOut} />
                </Field>
              )}
              <Field label={t('Plants')}>
                <input className="input w-24" type="number" min="1" max="100000" required value={qty} onChange={(e) => setQty(e.target.value)} />
              </Field>
              <Field label={t('Holds the cells until')}>
                <DateField value={until} onChange={setUntil} />
              </Field>
              <Button type="submit" variant="secondary">
                {t('Save')}
              </Button>
            </form>
          )}
        </div>
      )}
      {error && <ErrorMessage>{error}</ErrorMessage>}
    </div>
  )
}
