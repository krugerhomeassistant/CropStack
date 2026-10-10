import { useEffect, useRef, useState } from 'react'
import { Trash2 } from 'lucide-react'
import { api, type Bed, type BedIn, type BedKind, type CropSummary } from '../api'
import { t } from '../i18n'
import { useApp } from '../state'
import BedGrid from './BedGrid'
import { Button, ErrorMessage, Field, IconButton, Section, Skeleton, Switch } from './ui'

const SNAP = 0.1 // metres
const snap = (m: number) => Math.max(0, Math.round(m / SNAP) * SNAP)
const round = (n: number) => Math.round(n * 100) / 100
const MIN_DRAWN = 0.3 // a drag shorter than this in both directions is a click: place the default size

type Tool = 'select' | BedKind
const TOOLS: { tool: Tool; label: string; name?: string; width?: number; length?: number }[] = [
  { tool: 'select', label: 'Select and move' },
  { tool: 'bed', label: 'Draw bed', name: 'Bed', width: 1.2, length: 2.4 },
  { tool: 'row', label: 'Draw row', name: 'Row', width: 0.6, length: 5 },
  { tool: 'container', label: 'Draw pot', name: 'Pot', width: 0.5, length: 0.5 },
]

type Pt = { x: number; y: number }
type Rect = { x: number; y: number; width: number; length: number }
type Drag =
  | { k: 'move'; start: Pt; orig: Map<number, Pt> }
  | { k: 'resize'; id: number }
  | { k: 'draw'; start: Pt }

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
export default function LayoutEditor({ onChange }: { onChange: () => void }) {
  const { user } = useApp()
  const canEdit = user.role !== 'viewer'
  const [beds, setBeds] = useState<Bed[] | null>(null)
  const [selected, setSelected] = useState<number | null>(null)
  const [tool, setTool] = useState<Tool>('select')
  const [together, setTogether] = useState(true)
  const [draft, setDraft] = useState<Rect | null>(null)
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
    const p = point(e)
    if (d.k === 'draw') {
      const x = snap(p.x)
      const y = snap(p.y)
      setDraft({ x: Math.min(x, d.start.x), y: Math.min(y, d.start.y), width: Math.abs(x - d.start.x), length: Math.abs(y - d.start.y) })
    } else if (d.k === 'resize') {
      setBeds((bs) => bs && bs.map((b) => (b.id === d.id ? { ...b, width: Math.max(SNAP, round(snap(p.x) - b.x)), length: Math.max(SNAP, round(snap(p.y) - b.y)) } : b)))
    } else {
      const least = (axis: 'x' | 'y') => Math.min(...[...d.orig.values()].map((o) => o[axis]))
      const dx = Math.max(Math.round((p.x - d.start.x) / SNAP) * SNAP, -least('x'))
      const dy = Math.max(Math.round((p.y - d.start.y) / SNAP) * SNAP, -least('y'))
      setBeds((bs) => bs && bs.map((b) => (d.orig.has(b.id) ? { ...b, x: round(d.orig.get(b.id)!.x + dx), y: round(d.orig.get(b.id)!.y + dy) } : b)))
    }
  }
  function up() {
    const d = drag.current
    drag.current = null
    if (!d) return
    if (d.k === 'draw') {
      const r = draft
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
      const b = beds?.find((x) => x.id === d.id)
      if (b) api.updateBed(b.id, { width: b.width, length: b.length }).then(refresh, fail)
    } else {
      const moved = (beds ?? []).filter((b) => d.orig.has(b.id) && (b.x !== d.orig.get(b.id)!.x || b.y !== d.orig.get(b.id)!.y))
      Promise.all(moved.map((b) => api.updateBed(b.id, { x: b.x, y: b.y }))).catch(fail)
    }
  }

  const title = t('Garden plan')
  if (!beds) return error ? <Section title={title}><ErrorMessage>{error}</ErrorMessage></Section> : <Skeleton className="h-48" />

  const current = beds.find((b) => b.id === selected) ?? null
  const w = Math.max(10, ...beds.map((b) => b.x + b.width + 2))
  const h = Math.max(6, ...beds.map((b) => b.y + b.length + 2))
  const layouts = [...new Set(beds.map((b) => b.layout).filter(Boolean))]

  return (
    <Section title={title} description={canEdit ? t('Drawn to scale in metres. Pick a tool, then drag on the plan to draw. A click places the standard size.') : t('Drawn to scale in metres.')}>
      {error && <ErrorMessage>{error}</ErrorMessage>}
      {canEdit && (
        <div className="flex flex-wrap items-center gap-2">
          <div role="group" aria-label={t('Plan tools')} className="flex flex-wrap gap-2">
            {TOOLS.map((x) => (
              <Button key={x.tool} variant={tool === x.tool ? 'primary' : 'secondary'} aria-pressed={tool === x.tool} onClick={() => setTool(x.tool)}>
                {t(x.label)}
              </Button>
            ))}
          </div>
          {layouts.length > 0 && (
            <label className="flex min-h-11 items-center gap-2 text-sm">
              <Switch label={t('Beds in a layout move together')} checked={together} onChange={setTogether} />
              {t('Beds in a layout move together')}
            </label>
          )}
        </div>
      )}
      <svg
        ref={svg}
        viewBox={`0 0 ${w} ${h}`}
        className={`w-full touch-none rounded-[var(--radius-row)] bg-sunken ${tool === 'select' ? '' : 'cursor-crosshair'}`}
        role="img"
        aria-label={t('Plan of the garden beds')}
        onPointerDown={planDown}
        onPointerMove={move}
        onPointerUp={up}
      >
        <defs>
          <pattern id="grid" width="1" height="1" patternUnits="userSpaceOnUse">
            <path d="M1 0H0V1" fill="none" className="stroke-line" strokeWidth="0.02" />
          </pattern>
        </defs>
        <rect width={w} height={h} fill="url(#grid)" />
        {frames(beds).map((f) => (
          <g key={f.name}>
            <rect x={f.x} y={f.y} width={f.width} height={f.length} rx={0.1} fill="none" strokeDasharray="0.2 0.12" strokeWidth={0.03} className="stroke-muted pointer-events-none" />
            <text
              x={f.x + 0.1}
              y={f.y - 0.08}
              fontSize={0.32}
              className={`fill-muted select-none ${canEdit && tool === 'select' ? 'cursor-grab' : ''}`}
              onPointerDown={(e) => canEdit && tool === 'select' && startMove(e, f.ids, point(e))}
            >
              {f.name}
            </text>
          </g>
        ))}
        {beds.map((b) => (
          <g key={b.id} onPointerDown={(e) => bedDown(e, b)} className={canEdit && tool === 'select' ? 'cursor-grab' : ''}>
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
        {draft && <rect x={draft.x} y={draft.y} width={draft.width} height={draft.length} fill="none" strokeDasharray="0.15 0.1" strokeWidth={0.05} className="stroke-leaf pointer-events-none" />}
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
      {beds.length === 0 && <p className="text-sm text-muted">{canEdit ? t('No beds yet. Choose Draw bed, then drag on the plan.') : t('No beds have been drawn yet.')}</p>}

      {beds.length > 0 && (
        <ul className="flex flex-col divide-y divide-line text-sm">
          {beds.map((b) => (
            <li key={b.id} className="py-2">
              <button type="button" className="min-h-11 w-full text-left" onClick={() => setSelected(b.id)}>
                <span className="font-bold">{b.name}</span>
                <span className="text-muted">
                  {' '}
                  · {round(b.width)} × {round(b.length)} m · {t('{count} planted here', { count: b.plantings.length })}
                  {b.layout && ` · ${b.layout}`}
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

      {canEdit && current && (
        <BedForm key={`form${current.id}:${current.width}:${current.length}`} bed={current} layouts={layouts} onSaved={refresh} onDeleted={() => { setSelected(null); refresh() }} fail={fail} />
      )}
    </Section>
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
      <Field label={t('Cell size (cm)')} hint={t('Changing it clears where plants sit in this bed.')}>
        <input className="input w-24" type="number" min="5" max="100" step="5" required value={cell} onChange={(e) => setCell(e.target.value)} />
      </Field>
      <Button type="submit">{t('Save')}</Button>
      <IconButton icon={Trash2} label={t('Delete bed')} onClick={() => api.deleteBed(bed.id).then(onDeleted, fail)} />
    </form>
  )
}
