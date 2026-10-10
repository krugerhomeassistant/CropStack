import { useState } from 'react'
import { api, type Bed, type CropSummary, type Placement } from '../api'
import { t } from '../i18n'
import { useApp } from '../state'
import { Button, ErrorMessage, Field } from './ui'

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

/** The inside of one bed, cell by cell, on any date. Pick a crop and paint cells to plant it there from that date;
 *  the same cell can hold something else before or after, so a bed can be mixed and staggered. */
export default function BedGrid({ bed, crops, onChange }: { bed: Bed; crops: CropSummary[]; onChange: () => void }) {
  const canEdit = useApp().user.role !== 'viewer'
  const today = iso(new Date())
  const [on, setOn] = useState(today)
  const [brush, setBrush] = useState<Brush>(null)
  const [painted, setPainted] = useState<string[]>([])
  const [info, setInfo] = useState<Placement | null>(null)
  const [until, setUntil] = useState('')
  const [sow, setSow] = useState('')
  const [setOut, setSetOut] = useState('')
  const [qty, setQty] = useState('')
  const [error, setError] = useState('')

  const here = (c: number, r: number) =>
    bed.placements.filter((p) => p.cells.some(([x, y]) => x === c && y === r) && p.from <= on && on <= p.until)
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
    if (k && !painted.includes(k)) setPainted((p) => [...p, k])
  }
  function down(e: React.PointerEvent<SVGSVGElement>) {
    setError('')
    e.currentTarget.setPointerCapture(e.pointerId)
    if (brush && canEdit) return add(e)
    const k = at(e)
    const [c, r] = k ? k.split(',').map(Number) : [-1, -1]
    const p = here(c, r)[0] ?? null
    setInfo(p)
    setUntil(p?.until ?? '')
    setSow(p?.start_date ?? '')
    setSetOut(p?.set_out_date ?? '')
    setQty(p ? String(p.quantity) : '')
  }
  function up() {
    const cells = painted.map((k) => k.split(',').map(Number) as [number, number])
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
    api
      .addPlanting({
        crop: brush.crop,
        method: brush.method,
        start_date: transplant ? addDays(on, -7 * brush.weeks) : on,
        set_out_date: transplant ? on : null,
        bed_id: bed.id,
        cells,
        location: '',
        notes: '',
      })
      .then(onChange, fail)
  }

  const crop = brush && brush !== 'erase' ? brush : null
  const legend = [...new Map(bed.placements.map((p) => [p.crop, p.name])).entries()]

  return (
    <div className="flex flex-col gap-3 rounded-[var(--radius-row)] bg-sunken p-3">
      <div className="flex flex-wrap items-end gap-3">
        <Field label={t('Show the bed on')}>
          <input className="input" type="date" value={on} onChange={(e) => e.target.value && setOn(e.target.value)} />
        </Field>
        <Button variant="ghost" onClick={() => setOn(today)}>
          {t('Today')}
        </Button>
      </div>
      <input
        type="range"
        aria-label={t('Move through the year')}
        min={-60}
        max={365}
        value={Math.round((new Date(`${on}T00:00:00`).getTime() - new Date(`${today}T00:00:00`).getTime()) / 864e5)}
        onChange={(e) => setOn(addDays(today, Number(e.target.value)))}
      />

      {canEdit && (
      <div className="flex flex-wrap items-end gap-2">
        <Field label={t('Plant')}>
          <select
            className="input"
            value={crop?.crop ?? ''}
            onChange={(e) => setBrush(e.target.value ? { crop: e.target.value, method: crop?.method ?? 'direct', weeks: crop?.weeks ?? 5 } : null)}
          >
            <option value="">{brush === 'erase' ? t('Choose a crop') : t('Choose a crop to paint')}</option>
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
        <Button variant={brush === 'erase' ? 'primary' : 'secondary'} onClick={() => setBrush(brush === 'erase' ? null : 'erase')}>
          {t('Take out of cells')}
        </Button>
      </div>
      )}
      <p className="text-sm text-muted">
        {crop
          ? t('Drag across the cells to plant them from {date}. The same cells can hold something else before or after.', { date: show(on) })
          : brush === 'erase'
            ? t('Drag across cells to take what is growing there on {date} out of them.', { date: show(on) })
            : t('Tap a cell to see what is in it, or choose a crop to paint.')}
      </p>

      <svg
        viewBox={`0 0 ${bed.cols} ${bed.rows}`}
        style={{ maxWidth: `${bed.cols * 3.5}rem` }}
        className="w-full touch-none select-none rounded-[var(--radius-row)] bg-canvas"
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
            return (
              <g key={key(c, r)}>
                <rect
                  x={c + 0.03}
                  y={r + 0.03}
                  width={0.94}
                  height={0.94}
                  rx={0.08}
                  fill={marked ? (crop ? cropColour(crop.crop) : 'transparent') : p[0] ? cropColour(p[0].crop) : 'transparent'}
                  className={clashing.has(key(c, r)) ? 'stroke-danger' : marked ? 'stroke-ink' : 'stroke-line'}
                  strokeWidth={clashing.has(key(c, r)) || marked ? 0.08 : 0.03}
                  strokeDasharray={marked ? '0.15 0.1' : undefined}
                />
                {p[0] && (
                  <text x={c + 0.5} y={r + 0.6} textAnchor="middle" fontSize={0.32} className="pointer-events-none fill-ink">
                    {p[0].name.slice(0, 4)}
                  </text>
                )}
              </g>
            )
          }),
        )}
      </svg>
      <p className="text-sm text-muted">
        {t('One cell is {size} cm square.', { size: bed.cell_cm })}
        {legend.length > 0 && ` ${t('In this bed: {crops}.', { crops: legend.map(([, n]) => n).join(', ') })}`}
      </p>

      {info && (
        <div className="flex flex-col gap-2 rounded-[var(--radius-row)] bg-surface p-3 text-sm">
          <p className="font-bold">{info.name}</p>
          <p>
            {t('{count} plants in {cells} cells (room for {room}). Holds the cells from {from} to {until}.', {
              count: info.quantity,
              cells: info.cells.length,
              room: info.capacity,
              from: show(info.from),
              until: show(info.until),
            })}
          </p>
          {canEdit && (
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
