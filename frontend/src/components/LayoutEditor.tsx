import { useEffect, useRef, useState } from 'react'
import { LayoutGrid, Trash2 } from 'lucide-react'
import { api, type Bed, type BedIn, type BedKind, type CropSummary } from '../api'
import { t } from '../i18n'
import { useApp } from '../state'
import BedGrid from './BedGrid'
import { Button, EmptyState, ErrorMessage, Field, IconButton, Section, Skeleton } from './ui'

const SNAP = 0.1 // metres
const snap = (m: number) => Math.max(0, Math.round(m / SNAP) * SNAP)
const round = (n: number) => Math.round(n * 100) / 100

const TEMPLATES: { kind: BedKind; name: string; width: number; length: number; label: string }[] = [
  { kind: 'bed', name: 'Bed', width: 1.2, length: 2.4, label: 'Raised bed 1.2 × 2.4 m' },
  { kind: 'row', name: 'Row', width: 0.6, length: 5, label: 'Row 0.6 × 5 m' },
  { kind: 'container', name: 'Pot', width: 0.5, length: 0.5, label: 'Container 0.5 × 0.5 m' },
]

type Drag = { id: number; dx: number; dy: number }

/** The garden plan: beds drawn to scale in metres. Drag a bed to move it; select one to rename or resize it. */
export default function LayoutEditor({ onChange }: { onChange: () => void }) {
  const { user } = useApp()
  const canEdit = user.role !== 'viewer'
  const [beds, setBeds] = useState<Bed[] | null>(null)
  const [selected, setSelected] = useState<number | null>(null)
  const [crops, setCrops] = useState<CropSummary[]>([])
  const [error, setError] = useState('')
  const drag = useRef<Drag | null>(null)
  const svg = useRef<SVGSVGElement>(null)

  const load = () =>
    api.beds().then(setBeds, (e) => setError(e instanceof Error ? e.message : t('Failed to load')))
  useEffect(() => {
    load()
    api.crops().then(setCrops, () => setCrops([]))
  }, [])

  const fail = (e: unknown) => setError(e instanceof Error ? e.message : t('Failed to save'))
  const refresh = () => load().then(onChange)

  function add(tpl: (typeof TEMPLATES)[number]) {
    const right = Math.max(0, ...(beds ?? []).map((b) => b.x + b.width))
    const n = (beds ?? []).filter((b) => b.kind === tpl.kind).length + 1
    const body: BedIn = { name: `${t(tpl.name)} ${n}`, kind: tpl.kind, x: beds?.length ? snap(right + 0.4) : 0.5, y: 0.5, width: tpl.width, length: tpl.length, cell_cm: 30 }
    api.addBed(body).then((b) => {
      setSelected(b.id)
      return refresh()
    }, fail)
  }

  const point = (e: React.PointerEvent) => {
    const el = svg.current!
    const p = el.createSVGPoint()
    p.x = e.clientX
    p.y = e.clientY
    const m = p.matrixTransform(el.getScreenCTM()!.inverse())
    return { x: m.x, y: m.y }
  }

  function down(e: React.PointerEvent, b: Bed) {
    setSelected(b.id)
    if (!canEdit) return
    const p = point(e)
    drag.current = { id: b.id, dx: p.x - b.x, dy: p.y - b.y }
    ;(e.currentTarget as Element).setPointerCapture(e.pointerId)
  }
  function move(e: React.PointerEvent) {
    const d = drag.current
    if (!d) return
    const p = point(e)
    setBeds((bs) => bs && bs.map((b) => (b.id === d.id ? { ...b, x: round(snap(p.x - d.dx)), y: round(snap(p.y - d.dy)) } : b)))
  }
  function up() {
    const d = drag.current
    drag.current = null
    const b = beds?.find((x) => x.id === d?.id)
    if (b) api.updateBed(b.id, { x: b.x, y: b.y }).catch(fail)
  }

  const title = t('Garden plan')
  if (!beds) return error ? <Section title={title}><ErrorMessage>{error}</ErrorMessage></Section> : <Skeleton className="h-48" />

  const current = beds.find((b) => b.id === selected) ?? null
  const w = Math.max(8, ...beds.map((b) => b.x + b.width + 1))
  const h = Math.max(5, ...beds.map((b) => b.y + b.length + 1))

  return (
    <Section title={title} description={t('Drawn to scale in metres. Drag a bed to move it.')}>
      {error && <ErrorMessage>{error}</ErrorMessage>}
      {beds.length === 0 ? (
        <EmptyState icon={LayoutGrid} title={t('No beds yet')}>
          {canEdit ? t('Add a bed, container or row below, then give each planting a place.') : t('No beds have been drawn yet.')}
        </EmptyState>
      ) : (
        <svg
          ref={svg}
          viewBox={`0 0 ${w} ${h}`}
          className="w-full touch-none rounded-[var(--radius-row)] bg-sunken"
          role="img"
          aria-label={t('Plan of the garden beds')}
          onPointerMove={move}
          onPointerUp={up}
        >
          <defs>
            <pattern id="grid" width="1" height="1" patternUnits="userSpaceOnUse">
              <path d="M1 0H0V1" fill="none" className="stroke-line" strokeWidth="0.02" />
            </pattern>
          </defs>
          <rect width={w} height={h} fill="url(#grid)" />
          {beds.map((b) => (
            <g key={b.id} onPointerDown={(e) => down(e, b)} className={canEdit ? 'cursor-grab' : ''}>
              <rect
                x={b.x}
                y={b.y}
                width={b.width}
                height={b.length}
                rx={b.kind === 'container' ? Math.min(b.width, b.length) / 2 : 0.05}
                className={`${b.crowded ? 'fill-marigold/30 stroke-marigold' : 'fill-leaf/15 stroke-leaf'}`}
                strokeWidth={b.id === selected ? 0.1 : 0.04}
              />
              <text x={b.x + b.width / 2} y={b.y + b.length / 2} textAnchor="middle" fontSize={Math.min(0.35, b.width / 4)} className="fill-ink pointer-events-none select-none">
                {b.name}
              </text>
            </g>
          ))}
        </svg>
      )}

      {beds.length > 0 && (
        <ul className="flex flex-col divide-y divide-line text-sm">
          {beds.map((b) => (
            <li key={b.id} className="py-2">
              <button type="button" className="min-h-11 w-full text-left" onClick={() => setSelected(b.id)}>
                <span className="font-bold">{b.name}</span>
                <span className="text-muted">
                  {' '}
                  · {round(b.width)} × {round(b.length)} m · {t('{count} planted here', { count: b.plantings.length })}
                </span>
                {b.crowded && (
                  <span className="block font-semibold text-harvest">
                    {t('Too full: the plants need {need} m² and the bed is {area} m².', { need: b.needed_m2, area: b.area_m2 })}
                  </span>
                )}
              </button>
            </li>
          ))}
        </ul>
      )}

      {current && <BedGrid key={`grid${current.id}`} bed={current} crops={crops} onChange={refresh} />}

      {canEdit && current && <BedForm key={`form${current.id}`} bed={current} onSaved={refresh} onDeleted={() => { setSelected(null); refresh() }} fail={fail} />}

      {canEdit && (
        <div className="flex flex-wrap gap-2">
          {TEMPLATES.map((tpl) => (
            <Button key={tpl.kind} variant="secondary" onClick={() => add(tpl)}>
              {t('Add')} {t(tpl.label)}
            </Button>
          ))}
        </div>
      )}
    </Section>
  )
}

function BedForm({ bed, onSaved, onDeleted, fail }: { bed: Bed; onSaved: () => void; onDeleted: () => void; fail: (e: unknown) => void }) {
  const [name, setName] = useState(bed.name)
  const [width, setWidth] = useState(String(round(bed.width)))
  const [length, setLength] = useState(String(round(bed.length)))
  const [cell, setCell] = useState(String(bed.cell_cm))
  return (
    <form
      className="flex flex-wrap items-end gap-2 rounded-[var(--radius-row)] bg-sunken p-3"
      onSubmit={(e) => {
        e.preventDefault()
        api.updateBed(bed.id, { name, width: Number(width), length: Number(length), cell_cm: Number(cell) }).then(onSaved, fail)
      }}
    >
      <Field label={t('Name')}>
        <input className="input" required maxLength={60} value={name} onChange={(e) => setName(e.target.value)} />
      </Field>
      <Field label={t('Width (m)')}>
        <input className="input w-24" type="number" min="0.1" max="100" step="0.1" required value={width} onChange={(e) => setWidth(e.target.value)} />
      </Field>
      <Field label={t('Length (m)')}>
        <input className="input w-24" type="number" min="0.1" max="100" step="0.1" required value={length} onChange={(e) => setLength(e.target.value)} />
      </Field>
      <Field label={t('Cell size (cm)')} hint={t('Changing it clears where plants sit in this bed.')}>
        <input className="input w-24" type="number" min="5" max="100" step="5" required value={cell} onChange={(e) => setCell(e.target.value)} />
      </Field>
      <Button type="submit">{t('Save')}</Button>
      <IconButton icon={Trash2} label={t('Delete bed')} onClick={() => api.deleteBed(bed.id).then(onDeleted, fail)} />
    </form>
  )
}
