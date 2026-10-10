import { useEffect, useRef, useState } from 'react'
import { Circle, MousePointer2, RectangleHorizontal, Rows3, Trash2, type LucideIcon } from 'lucide-react'
import { api, type Bed, type BedIn, type BedKind, type CropSummary, type PlanItem, type Recommendation } from '../api'
import { t } from '../i18n'
import { useApp } from '../state'
import BedGrid from './BedGrid'
import { cropIcon } from './cropIcon'
import type { PlantRequest } from './Recommendations'
import { Button, ErrorMessage, Field, IconButton, Section, Skeleton, Switch } from './ui'

const SNAP = 0.1 // metres
const snap = (m: number) => Math.max(0, Math.round(m / SNAP) * SNAP)
const round = (n: number) => Math.round(n * 100) / 100
const MIN_DRAWN = 0.3 // a drag shorter than this in both directions is a click: place the default size

type Tool = 'select' | BedKind
const TOOLS: { tool: Tool; label: string; short: string; icon: LucideIcon; name?: string; width?: number; length?: number }[] = [
  { tool: 'select', label: 'Select and move', short: 'Move', icon: MousePointer2 },
  { tool: 'bed', label: 'Draw bed', short: 'Bed', icon: RectangleHorizontal, name: 'Bed', width: 1.2, length: 2.4 },
  { tool: 'row', label: 'Draw row', short: 'Row', icon: Rows3, name: 'Row', width: 0.6, length: 5 },
  { tool: 'container', label: 'Draw pot', short: 'Pot', icon: Circle, name: 'Pot', width: 0.5, length: 0.5 },
]

type Frame = { x0: number; y0: number; x1: number; y1: number }
type Pt = { x: number; y: number }
type Rect = { x: number; y: number; width: number; length: number }
// `to` is the latest result of the gesture, kept here rather than read back from state: a release can arrive before React has re-rendered.
type Drag =
  | { k: 'move'; start: Pt; orig: Map<number, Pt>; to?: Map<number, Pt> }
  | { k: 'resize'; id: number; to?: { width: number; length: number } }
  | { k: 'draw'; start: Pt; to?: Rect }

/** Beds of one layout, framed: the name is a handle that moves them all. */
function frames(beds: Bed[]) {
  const by = new Map<string, Bed[]>()
  for (const b of beds) if (b.layout) by.set(b.layout, [...(by.get(b.layout) ?? []), b])
  return [...by].map(([name, members]) => {
    const x = Math.min(...members.map((b) => b.x)) - 0.2
    const y = Math.min(...members.map((b) => b.y)) - 0.2
    return { name, ids: members.map((b) => b.id), x, y, width: Math.max(...members.map((b) => b.x + b.width)) + 0.2 - x, length: Math.max(...members.map((b) => b.y + b.length)) + 0.2 - y }
  })
}

/** The garden plan, drawn to scale in metres: draw beds by dragging, move or resize them, and group them into layouts. */
export default function LayoutEditor({ onChange, suggested, request, plan }: { onChange: () => void; suggested: Recommendation[]; request: PlantRequest | null; plan: PlanItem[] }) {
  const { user } = useApp()
  const today = new Date().toLocaleDateString('sv') // YYYY-MM-DD in local time
  const canEdit = user.role !== 'viewer'
  const [beds, setBeds] = useState<Bed[] | null>(null)
  const [selected, setSelected] = useState<number | null>(null)
  const [tool, setTool] = useState<Tool>('select')
  const [together, setTogether] = useState(true)
  const [draft, setDraft] = useState<Rect | null>(null)
  const [crops, setCrops] = useState<CropSummary[]>([])
  const [editBed, setEditBed] = useState(false)
  const [error, setError] = useState('')
  const drag = useRef<Drag | null>(null)
  const svg = useRef<SVGSVGElement>(null)
  const frame = useRef<Frame | null>(null)

  const load = () =>
    api.beds().then(setBeds, (e) => setError(e instanceof Error ? e.message : t('Failed to load')))
  useEffect(() => {
    if (request?.bedId) setSelected(request.bedId)
  }, [request])
  useEffect(() => {
    load()
    api.crops().then(setCrops, () => setCrops([]))
  }, [])

  const fail = (e: unknown) => setError(e instanceof Error ? e.message : t('Failed to save'))
  const refresh = () => load().then(onChange)

  const point = (e: React.PointerEvent): Pt => {
    const el = svg.current!
    const p = el.createSVGPoint()
    p.x = e.clientX
    p.y = e.clientY
    const m = p.matrixTransform(el.getScreenCTM()!.inverse())
    return { x: m.x, y: m.y }
  }
  const capture = (e: React.PointerEvent) => svg.current!.setPointerCapture(e.pointerId)

  function create(r: Rect, kind: BedKind) {
    const tpl = TOOLS.find((x) => x.tool === kind)!
    const n = (beds ?? []).filter((b) => b.kind === kind).length + 1
    const body: BedIn = { name: `${t(tpl.name!)} ${n}`, kind, x: round(r.x), y: round(r.y), width: round(r.width), length: round(r.length), cell_cm: 30, layout: '' }
    api.addBed(body).then((b) => {
      setSelected(b.id)
      return refresh()
    }, fail)
  }

  function startMove(e: React.PointerEvent, ids: number[], at: Pt) {
    e.stopPropagation()
    drag.current = { k: 'move', start: at, orig: new Map((beds ?? []).filter((b) => ids.includes(b.id)).map((b) => [b.id, { x: b.x, y: b.y }])) }
    capture(e)
  }
  function bedDown(e: React.PointerEvent, b: Bed) {
    if (tool !== 'select') return // let the plan start drawing
    setSelected(b.id)
    if (!canEdit) return
    const ids = together && b.layout ? (beds ?? []).filter((x) => x.layout === b.layout).map((x) => x.id) : [b.id]
    startMove(e, ids, point(e))
  }
  function planDown(e: React.PointerEvent) {
    if (tool === 'select') return setSelected(null)
    if (!canEdit) return
    const p = point(e)
    drag.current = { k: 'draw', start: { x: snap(p.x), y: snap(p.y) } }
    capture(e)
  }
  function move(e: React.PointerEvent) {
    const d = drag.current
    if (!d) return
    if (e.buttons === 0) return up() // the release was missed (left the window, lost capture): end the gesture
    const p = point(e)
    if (d.k === 'draw') {
      const x = snap(p.x)
      const y = snap(p.y)
      d.to = { x: Math.min(x, d.start.x), y: Math.min(y, d.start.y), width: Math.abs(x - d.start.x), length: Math.abs(y - d.start.y) }
      setDraft(d.to)
    } else if (d.k === 'resize') {
      const b = beds?.find((x) => x.id === d.id)
      if (!b) return
      d.to = { width: Math.max(SNAP, round(snap(p.x) - b.x)), length: Math.max(SNAP, round(snap(p.y) - b.y)) }
      setBeds((bs) => bs && bs.map((x) => (x.id === d.id ? { ...x, ...d.to! } : x)))
    } else {
      const least = (axis: 'x' | 'y') => Math.min(...[...d.orig.values()].map((o) => o[axis]))
      const dx = Math.max(Math.round((p.x - d.start.x) / SNAP) * SNAP, -least('x'))
      const dy = Math.max(Math.round((p.y - d.start.y) / SNAP) * SNAP, -least('y'))
      d.to = new Map([...d.orig].map(([id, o]) => [id, { x: round(o.x + dx), y: round(o.y + dy) }]))
      setBeds((bs) => bs && bs.map((b) => (d.to!.has(b.id) ? { ...b, ...d.to!.get(b.id)! } : b)))
    }
  }
  function up() {
    const d = drag.current
    drag.current = null
    if (!d) return
    if (d.k === 'draw') {
      const r = d.to
      setDraft(null)
      if (!r) {
        // a plain click: the default size for the tool, with its corner where it was clicked
        const tpl = TOOLS.find((x) => x.tool === tool)!
        setTool('select')
        return create({ x: d.start.x, y: d.start.y, width: tpl.width!, length: tpl.length! }, tool as BedKind)
      }
      const tpl = TOOLS.find((x) => x.tool === tool)!
      const tiny = r.width < MIN_DRAWN && r.length < MIN_DRAWN
      create(tiny ? { x: r.x, y: r.y, width: tpl.width!, length: tpl.length! } : { ...r, width: Math.max(r.width, 0.2), length: Math.max(r.length, 0.2) }, tool as BedKind)
      setTool('select')
    } else if (d.k === 'resize') {
      if (d.to) api.updateBed(d.id, d.to).then(refresh, fail)
    } else {
      const moved = [...(d.to ?? [])].filter(([id, to]) => to.x !== d.orig.get(id)!.x || to.y !== d.orig.get(id)!.y)
      Promise.all(moved.map(([id, to]) => api.updateBed(id, to))).catch(fail)
    }
  }

  if (!beds) return error ? <ErrorMessage>{error}</ErrorMessage> : <Skeleton className="h-48" />

  const current = beds.find((b) => b.id === selected) ?? null
  // The map is framed on the beds (a metre or two around them), and held still while one is being dragged.
  const framed = (): Frame => {
    const x0 = beds.length ? Math.max(0, Math.min(...beds.map((b) => b.x)) - 1) : 0
    const y0 = beds.length ? Math.max(0, Math.min(...beds.map((b) => b.y)) - 1) : 0
    return { x0, y0, x1: Math.max(x0 + 5, ...beds.map((b) => b.x + b.width + 1.5)), y1: Math.max(y0 + 4.5, ...beds.map((b) => b.y + b.length + 2.6)) }
  }
  const f = drag.current && frame.current ? frame.current : (frame.current = framed())
  const layouts = [...new Set(beds.map((b) => b.layout).filter(Boolean))]

  const status = (b: Bed) =>
    b.clashes.length
      ? t('{count} cells have two plantings at once', { count: b.clashes.length })
      : b.over_capacity.length
        ? t('More plants than the cells hold')
        : b.needed_m2 > b.area_m2
          ? t('Too full: the plants need {need} m² and the bed is {area} m².', { need: b.needed_m2, area: b.area_m2 })
          : ''

  return (
    <div className="grid grid-cols-[minmax(0,1fr)] gap-4 lg:grid-cols-[minmax(0,3fr)_minmax(0,2fr)] lg:items-start">
      <div className="lg:sticky lg:top-4">
      <Section>
        {error && <ErrorMessage>{error}</ErrorMessage>}
      {canEdit && current?.layout && (
        <label className="flex min-h-11 items-center gap-2 text-sm">
          <Switch label={t('Beds in a layout move together')} checked={together} onChange={setTogether} />
          {t('Beds in a layout move together')}
        </label>
      )}
      <div className="relative overflow-hidden rounded-[var(--radius-section)] border border-line bg-sunken">
      <svg
        ref={svg}
        viewBox={`${f.x0} ${f.y0} ${f.x1 - f.x0} ${f.y1 - f.y0}`}
        className={`block max-h-[70dvh] w-full touch-none ${tool === 'select' ? '' : 'cursor-crosshair'}`}
        role="img"
        aria-label={t('Plan of the garden beds')}
        onPointerDown={planDown}
        onPointerMove={move}
        onPointerUp={up}
        onPointerCancel={up}
      >
        <defs>
          <pattern id="dots" width="1" height="1" patternUnits="userSpaceOnUse">
            <path d="M0.5 0.42V0.58M0.42 0.5H0.58" className="stroke-feed/40" strokeWidth="0.03" fill="none" />
          </pattern>
        </defs>
        <rect x={f.x0} y={f.y0} width={f.x1 - f.x0} height={f.y1 - f.y0} fill="url(#dots)" />
        {frames(beds).map((fr) => (
          <g key={fr.name}>
            <rect x={fr.x} y={fr.y} width={fr.width} height={fr.length} rx={0.15} fill="none" strokeDasharray="0.2 0.12" strokeWidth={0.03} className="stroke-muted pointer-events-none" />
            <text
              x={fr.x + 0.12}
              y={fr.y + fr.length + 0.34}
              fontSize={0.26}
              className={`fill-muted select-none ${canEdit && tool === 'select' ? 'cursor-grab' : ''}`}
              onPointerDown={(e) => canEdit && tool === 'select' && startMove(e, fr.ids, point(e))}
            >
              {fr.name}
            </text>
          </g>
        ))}
        {beds.map((b) => {
          const cell = b.cell_cm / 100
          const live = b.placements.filter((p) => p.from <= today && today <= p.until)
          const growing = live.filter((p) => p.status !== 'planned')
          const waiting = b.placements.filter((p) => p.status === 'planned' || p.from > today)
          const isPot = b.kind === 'container'
          const size = Math.min(cell * 0.78, 0.5)
          const label = waiting.length > 0 ? `${b.name}  ⏳${waiting.length}` : b.name
          const tag = Math.max(0.9, label.length * 0.15 + 0.3)
          const mark = (p: (typeof growing)[number], faded: boolean) =>
            p.cells.map(([c, r]) => (
              <text key={`${faded ? 'w' : 'g'}${p.planting_id}${c},${r}`} x={b.x + (c + 0.5) * cell} y={b.y + (r + 0.5) * cell + size * 0.34} fontSize={size} textAnchor="middle" opacity={faded ? 0.4 : 1}>
                {cropIcon(p.crop)}
              </text>
            ))
          return (
            <g key={b.id} onPointerDown={(e) => bedDown(e, b)} className={canEdit && tool === 'select' ? 'cursor-grab' : ''}>
              <clipPath id={`clip${b.id}`}>
                {isPot ? <ellipse cx={b.x + b.width / 2} cy={b.y + b.length / 2} rx={b.width / 2} ry={b.length / 2} /> : <rect x={b.x} y={b.y} width={b.width} height={b.length} rx={0.06} />}
              </clipPath>
              {b.id === selected && (isPot ? <ellipse cx={b.x + b.width / 2} cy={b.y + b.length / 2} rx={b.width / 2 + 0.14} ry={b.length / 2 + 0.14} fill="none" className="stroke-leaf pointer-events-none" strokeWidth={0.07} /> : <rect x={b.x - 0.14} y={b.y - 0.14} width={b.width + 0.28} height={b.length + 0.28} rx={0.14} fill="none" className="stroke-leaf pointer-events-none" strokeWidth={0.07} />)}
              {isPot ? (
                <ellipse cx={b.x + b.width / 2} cy={b.y + b.length / 2} rx={b.width / 2} ry={b.length / 2} className="fill-feed/25 stroke-feed" strokeWidth={0.09} />
              ) : (
                <rect x={b.x} y={b.y} width={b.width} height={b.length} rx={0.06} className="fill-feed/25 stroke-feed" strokeWidth={0.09} />
              )}
              <g clipPath={`url(#clip${b.id})`} className="pointer-events-none select-none">
                {waiting.flatMap((p) =>
                  p.cells.map(([c, r]) => (
                    <rect key={`o${p.planting_id}${c},${r}`} x={b.x + c * cell + 0.03} y={b.y + r * cell + 0.03} width={cell - 0.06} height={cell - 0.06} rx={0.04} fill="none" className="stroke-leaf" strokeDasharray="0.08 0.06" strokeWidth={0.03} />
                  )),
                )}
                {waiting.map((p) => mark(p, true))}
                {growing.map((p) => mark(p, false))}
              </g>
              {b.crowded && <rect x={b.x} y={b.y} width={b.width} height={b.length} rx={0.06} fill="none" className="stroke-marigold pointer-events-none" strokeDasharray="0.18 0.1" strokeWidth={0.06} />}
              <g className="pointer-events-none select-none">
                <rect x={b.x} y={b.y - 0.46} width={tag} height={0.34} rx={0.17} className="fill-surface stroke-line" strokeWidth={0.02} />
                <text x={b.x + tag / 2} y={b.y - 0.46 + 0.24} textAnchor="middle" fontSize={0.2} className="fill-ink font-semibold">
                  {label}
                </text>
              </g>
            </g>
          )
        })}
        {draft && <rect x={draft.x} y={draft.y} width={draft.width} height={draft.length} rx={0.06} fill="none" strokeDasharray="0.15 0.1" strokeWidth={0.05} className="stroke-leaf pointer-events-none" />}
        <g className="pointer-events-none">
          <path d={`M${f.x1 - 1.3} ${f.y1 - 0.3}H${f.x1 - 0.3}M${f.x1 - 1.3} ${f.y1 - 0.38}V${f.y1 - 0.22}M${f.x1 - 0.3} ${f.y1 - 0.38}V${f.y1 - 0.22}`} className="stroke-muted" strokeWidth={0.04} fill="none" />
          <text x={f.x1 - 0.8} y={f.y1 - 0.42} textAnchor="middle" fontSize={0.2} className="fill-muted">
            1 m
          </text>
        </g>
        {canEdit && tool === 'select' && current && (
          <g
            className="cursor-nwse-resize"
            onPointerDown={(e) => {
              e.stopPropagation()
              drag.current = { k: 'resize', id: current.id }
              capture(e)
            }}
          >
            <circle data-testid="resize-handle" cx={current.x + current.width} cy={current.y + current.length} r={0.6} fill="transparent" />
            <circle cx={current.x + current.width} cy={current.y + current.length} r={0.2} className="fill-surface stroke-leaf" strokeWidth={0.06} />
          </g>
        )}
      </svg>
      {canEdit && (
        <div className="pointer-events-none absolute inset-x-0 bottom-3 flex justify-center">
          <div role="group" aria-label={t('Plan tools')} className="pointer-events-auto flex max-w-full gap-0.5 rounded-full border border-line bg-surface p-1 shadow-lg">
            {TOOLS.map((x) => (
              <button
                key={x.tool}
                type="button"
                aria-pressed={tool === x.tool}
                aria-label={t(x.label)}
                onClick={() => setTool(x.tool)}
                className={`flex min-h-11 items-center gap-1 rounded-full px-2.5 text-sm font-semibold ${tool === x.tool ? 'bg-leaf text-on-leaf' : 'text-ink hover:bg-sunken'}`}
              >
                <x.icon className="size-4 shrink-0" aria-hidden />
                {t(x.short)}
              </button>
            ))}
          </div>
        </div>
      )}
      </div>
        {beds.some((b) => b.placements.length > 0) && <p className="text-xs text-muted">{t('Filled cells are growing now; dashed cells are planned. ⏳ counts what is still to plant.')}</p>}
        {beds.length === 0 && <p className="text-sm text-muted">{canEdit ? t('No beds yet. Choose Draw bed, then drag on the plan.') : t('No beds have been drawn yet.')}</p>}
        {beds.length > 0 && (
          <div className="flex gap-2 overflow-x-auto pb-1" role="group" aria-label={t('Beds')}>
            {beds.map((b) => (
              <button
                key={b.id}
                type="button"
                aria-pressed={b.id === selected}
                onClick={() => setSelected(b.id)}
                className={`min-h-11 shrink-0 rounded-full border px-4 text-sm font-semibold ${b.id === selected ? 'border-leaf bg-leaf/15' : 'border-line bg-surface'} ${b.crowded ? 'text-harvest' : ''}`}
              >
                {b.name}
                {(() => {
                  const live = b.placements.filter((p) => p.from <= today && today <= p.until && p.status !== 'planned')
                  const wait = b.placements.filter((p) => p.status === 'planned' || p.from > today).length
                  const icons = [...new Set(live.map((p) => cropIcon(p.crop)))].slice(0, 3).join('')
                  return icons || wait ? <span className="ml-2 font-normal" aria-hidden>{icons}{wait > 0 && ` ⏳${wait}`}</span> : null
                })()}
              </button>
            ))}
          </div>
        )}
      </Section>
      </div>

      {current ? (
        <Section
          title={current.name}
          description={<span className={status(current) ? 'font-semibold text-harvest' : ''}>{status(current) || `${round(current.width)} × ${round(current.length)} m${current.layout ? ` · ${current.layout}` : ''}`}</span>}
          action={
            canEdit && (
              <Button variant="ghost" onClick={() => setEditBed(!editBed)}>
                {editBed ? t('Close') : t('Edit bed')}
              </Button>
            )
          }
        >
          {canEdit && editBed && (
            <BedForm key={`form${current.id}:${current.width}:${current.length}`} bed={current} layouts={layouts} onSaved={refresh} onDeleted={() => { setSelected(null); refresh() }} fail={fail} />
          )}
          <BedGrid key={`grid${current.id}`} bed={current} crops={crops} suggested={suggested} plan={plan.filter((i) => i.bed_id === current.id)} request={request && (request.bedId === null || request.bedId === current.id) ? request : null} onChange={refresh} />
        </Section>
      ) : (
        beds.length > 0 && <p className="px-1 text-sm text-muted">{t('Tap a bed to plant in it.')}</p>
      )}
    </div>
  )
}

function BedForm({ bed, layouts, onSaved, onDeleted, fail }: { bed: Bed; layouts: string[]; onSaved: () => void; onDeleted: () => void; fail: (e: unknown) => void }) {
  const [name, setName] = useState(bed.name)
  const [width, setWidth] = useState(String(round(bed.width)))
  const [length, setLength] = useState(String(round(bed.length)))
  const [cell, setCell] = useState(String(bed.cell_cm))
  const [layout, setLayout] = useState(bed.layout)
  return (
    <form
      className="flex flex-wrap items-end gap-2 rounded-[var(--radius-row)] bg-sunken p-3"
      onSubmit={(e) => {
        e.preventDefault()
        api.updateBed(bed.id, { name, width: Number(width), length: Number(length), cell_cm: Number(cell), layout: layout.trim() }).then(onSaved, fail)
      }}
    >
      <Field label={t('Name')}>
        <input className="input" required maxLength={60} value={name} onChange={(e) => setName(e.target.value)} />
      </Field>
      <Field label={t('Layout')} hint={t('Beds with the same layout move together on the plan.')}>
        <input className="input" list="layouts" maxLength={60} value={layout} onChange={(e) => setLayout(e.target.value)} />
      </Field>
      <datalist id="layouts">
        {layouts.map((l) => (
          <option key={l} value={l} />
        ))}
      </datalist>
      <Field label={t('Width (m)')}>
        <input className="input w-24" type="number" min="0.1" max="100" step="0.1" required value={width} onChange={(e) => setWidth(e.target.value)} />
      </Field>
      <Field label={t('Length (m)')}>
        <input className="input w-24" type="number" min="0.1" max="100" step="0.1" required value={length} onChange={(e) => setLength(e.target.value)} />
      </Field>
      <Field label={t('Cell size (cm)')} hint={t('Plants keep their place; the cells are redrawn to the new size.')}>
        <input className="input w-24" type="number" min="5" max="100" step="5" required value={cell} onChange={(e) => setCell(e.target.value)} />
      </Field>
      <Button type="submit">{t('Save')}</Button>
      <IconButton icon={Trash2} label={t('Delete bed')} onClick={() => api.deleteBed(bed.id).then(onDeleted, fail)} />
    </form>
  )
}
