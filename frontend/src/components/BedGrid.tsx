import { useEffect, useRef, useState } from 'react'
import { ChevronLeft, ChevronRight, Eraser } from 'lucide-react'
import { api, type Bed, type CropSummary, type Placement, type PlanItem, type Recommendation } from '../api'
import { t } from '../i18n'
import { useApp } from '../state'
import { CropSheet, toRequest, type PlantRequest } from './Recommendations'
import { cropIcon } from './cropIcon'
import { Button, ErrorMessage, Field, IconButton } from './ui'

const iso = (d: Date) => `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}-${String(d.getDate()).padStart(2, '0')}`
const addDays = (s: string, n: number) => iso(new Date(new Date(`${s}T00:00:00`).getTime() + n * 864e5))
const key = (c: number, r: number) => `${c},${r}`
const show = (s: string) => new Date(`${s}T00:00:00`).toLocaleDateString(undefined, { day: 'numeric', month: 'short', year: 'numeric' })

/** A steady colour for each crop, so the same crop looks the same everywhere. */
export function cropColour(slug: string): string {
  let h = 0
  for (const ch of slug) h = (h * 31 + ch.charCodeAt(0)) % 360
  return `hsl(${h} 55% 55% / 0.5)`
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
  onChange,
}: {
  bed: Bed
  crops: CropSummary[]
  suggested: Recommendation[]
  request: PlantRequest | null
  plan: PlanItem[]
  onChange: () => void
}) {
  const canEdit = useApp().user.role !== 'viewer'
  const today = iso(new Date())
  const [on, setOn] = useState(request?.date ?? today)
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

  // arriving from a recommendation: the crop is chosen and the date set
  useEffect(() => {
    if (!request) return
    setBrush({ crop: request.crop, method: request.method, weeks: request.weeks })
    setOn(request.date)
  }, [request])

  const here = (c: number, r: number) =>
    bed.placements.filter((p) => p.cells.some(([x, y]) => x === c && y === r) && p.from <= on && on <= p.until)
  // the drafted year plan, shown dashed on cells that are empty on this date
  const ghost = (c: number, r: number) =>
    plan.find((i) => i.cells.some(([x, y]) => x === c && y === r) && (i.set_out_date ?? i.start_date) <= on && on <= i.until)
  const clashing = new Set(bed.clashes.map((x) => key(x.cell[0], x.cell[1])))
  const fail = (e: unknown) => setError(e instanceof Error ? e.message : t('Failed to save'))

  const at = (e: React.PointerEvent<SVGSVGElement>) => {
    const box = e.currentTarget.getBoundingClientRect()
    const c = Math.floor(((e.clientX - box.left) / box.width) * bed.cols)
    const r = Math.floor(((e.clientY - box.top) / box.height) * bed.rows)
    return c >= 0 && r >= 0 && c < bed.cols && r < bed.rows ? key(c, r) : null
  }
  function add(e: React.PointerEvent<SVGSVGElement>) {
    const k = at(e)
    if (k && !strokeRef.current.includes(k)) {
      strokeRef.current = [...strokeRef.current, k]
      setPainted(strokeRef.current)
    }
  }
  function down(e: React.PointerEvent<SVGSVGElement>) {
    setError('')
    e.currentTarget.setPointerCapture(e.pointerId)
    if (brush && canEdit) return add(e)
    const k = at(e)
    const [c, r] = k ? k.split(',').map(Number) : [-1, -1]
    const p = here(c, r)[0] ?? null
    setInfo(p)
    setEditing(false)
    setUntil(p?.until ?? '')
    setSow(p?.start_date ?? '')
    setSetOut(p?.set_out_date ?? '')
    setQty(p ? String(p.quantity) : '')
  }
  function up() {
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
        .updatePlanting(same.planting_id, { cells: union, quantity: Math.max(1, Math.round((same.quantity * union.length) / same.cells.length)) })
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
  const legend = [...new Map(bed.placements.map((p) => [p.crop, p.name])).entries()]
  const chips = suggested.slice(0, SUGGESTED)
  const nameOf = (slug: string) => crops.find((c) => c.slug === slug)?.names.en?.[0] ?? slug
  const pick = (r: Recommendation) => {
    const q = toRequest(r)
    setBrush(crop?.crop === r.crop ? null : { crop: q.crop, method: q.method, weeks: q.weeks })
  }

  return (
    <div className="flex flex-col gap-4">
      <div className="flex flex-col gap-1">
        <p className="text-sm font-semibold">{t('Date')}</p>
        <div className="flex items-center gap-1">
          <IconButton icon={ChevronLeft} label={t('A week earlier')} onClick={() => setOn(addDays(on, -7))} />
          <input className="input w-auto flex-1" type="date" aria-label={t('Show the bed on')} value={on} onChange={(e) => e.target.value && setOn(e.target.value)} />
          <IconButton icon={ChevronRight} label={t('A week later')} onClick={() => setOn(addDays(on, 7))} />
          {on !== today && (
            <Button variant="ghost" onClick={() => setOn(today)}>
              {t('Today')}
            </Button>
          )}
        </div>
        {canEdit && on < today && (
          <p className="text-sm text-muted">{t('Already growing? Plant on the day it went in and it is recorded as sown (or set out), with its harvest worked out from then.')}</p>
        )}
      </div>

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
                  {cropIcon(r.crop)}
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
              {t('Harvest from about {date}', { date: show(r.harvest_from) })} · {t('{n} per cell', { n: r.plants_per_cell })}
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

      <div className="mx-auto w-full rounded-xl border-[5px] border-feed/70 bg-feed/15 p-0.5" style={{ maxWidth: `${bed.cols * 4.5}rem` }}>
      <svg
        viewBox={`0 0 ${bed.cols} ${bed.rows}`}
        className="block w-full touch-none select-none"
        role="img"
        aria-label={t('Cells of {bed}', { bed: bed.name })}
        onPointerDown={down}
        onPointerMove={(e) => brush && canEdit && e.buttons && add(e)}
        onPointerUp={up}
      >
        {Array.from({ length: bed.rows }, (_, r) =>
          Array.from({ length: bed.cols }, (_, c) => {
            const p = here(c, r)
            const marked = painted.includes(key(c, r))
            const g = p[0] ? undefined : ghost(c, r)
            return (
              <g key={key(c, r)}>
                <rect
                  x={c + 0.03}
                  y={r + 0.03}
                  width={0.94}
                  height={0.94}
                  rx={0.08}
                  fill={marked ? (crop ? cropColour(crop.crop) : 'transparent') : p[0] ? cropColour(p[0].crop) : g ? cropColour(g.crop) : 'transparent'}
                  fillOpacity={g && !marked ? 0.45 : 1}
                  className={clashing.has(key(c, r)) ? 'stroke-danger' : marked || g ? 'stroke-ink' : 'stroke-feed/30'}
                  strokeWidth={clashing.has(key(c, r)) || marked || g ? 0.08 : 0.03}
                  strokeDasharray={marked || g ? '0.15 0.1' : undefined}
                />
                {(p[0] || g) && (
                  <text textAnchor="middle" className="pointer-events-none fill-ink">
                    <tspan x={c + 0.5} y={r + 0.52} fontSize={0.4}>
                      {cropIcon((p[0] ?? g!).crop)}
                    </tspan>
                    <tspan x={c + 0.5} y={r + 0.82} fontSize={0.2}>
                      {(p[0]?.name ?? g!.name).slice(0, 6)}
                    </tspan>
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
        {plan.length > 0 && ` ${t('Dashed cells are the drafted plan; step the date to see it through the year.')}`}
        {bed.outside > 0 && ` ${t('{n} planted cells sit beyond the edge of this bed; make the bed bigger to see them.', { n: bed.outside })}`}
        {legend.length > 0 && ` ${t('In this bed: {crops}.', { crops: legend.map(([, n]) => n).join(', ') })}`}
      </p>

      {info && (
        <div className="flex flex-col gap-2 rounded-[var(--radius-row)] bg-sunken p-3 text-sm">
          <div className="flex items-start justify-between gap-3">
            <div>
              <p className="font-bold">{info.name}</p>
              <p className="text-muted">
                {t('{count} plants · {from} to {until}', { count: info.quantity, from: show(info.from), until: show(info.until) })}
              </p>
              {info.harvest_from && info.harvest_to && (
                <p>{t('Harvest expected {from} to {to}', { from: show(info.harvest_from), to: show(info.harvest_to) })}</p>
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
                <input className="input" type="date" required value={sow} onChange={(e) => setSow(e.target.value)} />
              </Field>
              {info.method === 'transplant' && (
                <Field label={t('Set-out date')}>
                  <input className="input" type="date" required value={setOut} onChange={(e) => setSetOut(e.target.value)} />
                </Field>
              )}
              <Field label={t('Plants')}>
                <input className="input w-24" type="number" min="1" max="100000" required value={qty} onChange={(e) => setQty(e.target.value)} />
              </Field>
              <Field label={t('Holds the cells until')}>
                <input className="input" type="date" value={until} onChange={(e) => setUntil(e.target.value)} />
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
