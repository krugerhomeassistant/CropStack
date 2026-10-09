/**
 * Small dependency-free SVG charts for the climate page (docs/DESIGN.md, dataviz rules): 2 px lines, ~10 % bands,
 * hairline grid, a crosshair tooltip that also works from the keyboard, a legend for two or more series, and a table
 * view so nothing depends on hovering.
 */
import { useId, useLayoutEffect, useRef, useState, type KeyboardEvent, type PointerEvent, type RefObject } from 'react'
import { t } from '../i18n'

const M = { l: 44, r: 12, t: 16, b: 28 }
/** Chart size in CSS pixels, so axis text stays 11 px on a phone instead of shrinking with the drawing. */
const dims = (width: number) => {
  const W = Math.max(280, Math.round(width))
  const H = Math.round(Math.min(260, Math.max(190, W * 0.4)))
  return { W, H, PW: W - M.l - M.r, PH: H - M.t - M.b }
}
type Dim = ReturnType<typeof dims>

function useDim(): [RefObject<HTMLDivElement | null>, Dim] {
  const ref = useRef<HTMLDivElement>(null)
  const [width, setWidth] = useState(640)
  useLayoutEffect(() => {
    const el = ref.current
    if (!el) return
    setWidth(el.clientWidth || 640)
    const ro = new ResizeObserver(([e]) => setWidth(e.contentRect.width))
    ro.observe(el)
    return () => ro.disconnect()
  }, [])
  return [ref, dims(width)]
}
const DAYS_IN_MONTH = [31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31]
const MONTH_START = DAYS_IN_MONTH.map((_, m) => DAYS_IN_MONTH.slice(0, m).reduce((a, b) => a + b, 0))
// A non-leap year: the engine drops 29 Feb, so day i of every chart is the same calendar day.
const dayDate = (i: number) => new Date(2001, 0, 1 + i)
const monthShort = (m: number) => new Date(2001, m, 15).toLocaleDateString(undefined, { month: 'short' })
const monthLong = (m: number) => new Date(2001, m, 15).toLocaleDateString(undefined, { month: 'long' })
const dayLabel = (i: number) => dayDate(i).toLocaleDateString(undefined, { day: 'numeric', month: 'long' })

export type Series = {
  name: string
  /** A CSS colour, normally a chart token such as `var(--color-chart-warm)`. */
  color: string
  values: (number | null)[]
  /** Optional range drawn as a light band behind the line. */
  low?: (number | null)[]
  high?: (number | null)[]
}

/** Round axis ticks: 1, 2 or 5 times a power of ten. */
function niceTicks(min: number, max: number, count = 4) {
  const span = max - min || 1
  const raw = span / count
  const pow = 10 ** Math.floor(Math.log10(raw))
  const step = ([1, 2, 5, 10].find((m) => m * pow >= raw) ?? 10) * pow
  const lo = Math.floor(min / step) * step
  const hi = Math.ceil(max / step) * step
  const ticks: number[] = []
  for (let v = lo; v <= hi + step / 2; v += step) ticks.push(+v.toFixed(6))
  return { ticks, min: lo, max: hi }
}

const nums = (a?: (number | null)[]) => (a ?? []).filter((v): v is number => v !== null)

/** SVG path through the points, breaking the line where a value is missing. */
function linePath(values: (number | null)[], x: (i: number) => number, y: (v: number) => number) {
  let d = ''
  let pen = false
  values.forEach((v, i) => {
    if (v === null) pen = false
    else {
      d += `${pen ? 'L' : 'M'}${x(i).toFixed(1)} ${y(v).toFixed(1)}`
      pen = true
    }
  })
  return d
}

function bandPath(low: (number | null)[], high: (number | null)[], x: (i: number) => number, y: (v: number) => number) {
  const idx = low.map((_, i) => i).filter((i) => low[i] !== null && high[i] !== null)
  if (!idx.length) return ''
  const up = idx.map((i) => `${x(i).toFixed(1)} ${y(high[i] as number).toFixed(1)}`)
  const down = [...idx].reverse().map((i) => `${x(i).toFixed(1)} ${y(low[i] as number).toFixed(1)}`)
  return `M${up.join('L')}L${down.join('L')}Z`
}

function Legend({ items }: { items: { name: string; color: string }[] }) {
  if (items.length < 2) return null // one series: the title already says what is plotted
  return (
    <ul className="flex flex-wrap gap-x-4 gap-y-1 text-sm text-muted">
      {items.map((s) => (
        <li key={s.name} className="flex items-center gap-2">
          <span aria-hidden className="h-0.5 w-4 rounded-full" style={{ background: s.color }} />
          {s.name}
        </li>
      ))}
    </ul>
  )
}

function Tooltip({ d: { W, PW }, at, title, rows }: { d: Dim; at: number; title: string; rows: { name: string; color: string; value: string }[] }) {
  const pct = ((M.l + at * PW) / W) * 100
  return (
    <div
      role="status"
      className="pointer-events-none absolute top-1 z-10 min-w-36 rounded-[var(--radius-row)] border border-line bg-surface px-3 py-2 text-sm shadow-[0_4px_16px_rgb(0_0_0/0.12)]"
      style={{ left: `${pct}%`, transform: `translateX(${pct > 60 ? 'calc(-100% - 12px)' : '12px'})` }}
    >
      <p className="text-muted">{title}</p>
      {rows.map((r) => (
        <p key={r.name} className="flex items-center gap-2">
          <span aria-hidden className="h-0.5 w-3 rounded-full" style={{ background: r.color }} />
          <span className="font-bold">{r.value}</span>
          <span className="text-muted">{r.name}</span>
        </p>
      ))}
    </div>
  )
}

function TableView({ head, rows }: { head: string[]; rows: string[][] }) {
  return (
    <details className="text-sm">
      <summary className="cursor-pointer text-muted hover:text-ink">{t('Show as a table')}</summary>
      <div className="mt-2 overflow-x-auto">
        <table className="w-full min-w-72 text-left">
          <thead>
            <tr className="text-muted">
              {head.map((h) => (
                <th key={h} className="py-1 pr-4 font-semibold">
                  {h}
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {rows.map((r) => (
              <tr key={r[0]} className="border-t border-line">
                {r.map((c, i) => (
                  <td key={i} className="py-1 pr-4">
                    {c}
                  </td>
                ))}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </details>
  )
}

function Axes({ d: { W, H, PW }, ticks, y, format, months }: { d: Dim; ticks: number[]; y: (v: number) => number; format: (v: number) => string; months: boolean }) {
  return (
    <>
      {ticks.map((v) => (
        <g key={v}>
          <line x1={M.l} x2={W - M.r} y1={y(v)} y2={y(v)} className="stroke-line" strokeWidth={1} />
          <text x={M.l - 8} y={y(v)} dy="0.32em" textAnchor="end" className="fill-muted text-[11px]">
            {format(v)}
          </text>
        </g>
      ))}
      {months &&
        MONTH_START.map((d, m) => (
          <text key={m} x={M.l + ((d + DAYS_IN_MONTH[m] / 2) / 365) * PW} y={H - 8} textAnchor="middle" className="fill-muted text-[11px]">
            {monthShort(m)}
          </text>
        ))}
    </>
  )
}

/** Lines (with optional bands) over the 365 days of a typical year. */
export function YearChart({
  title,
  series,
  format,
  axisFormat = format,
  yMin,
  yMax,
  todayIndex,
}: {
  title: string
  series: Series[]
  /** Value with its unit, for the tooltip and table. */
  format: (v: number) => string
  /** Compact form for the axis. */
  axisFormat?: (v: number) => string
  yMin?: number
  yMax?: number
  /** Day of the year (0-364) to mark. */
  todayIndex?: number
}) {
  const [idx, setIdx] = useState<number | null>(null)
  const [box, d] = useDim()
  const { W, H, PW, PH } = d
  const descId = useId()
  const all = series.flatMap((s) => [...nums(s.values), ...nums(s.low), ...nums(s.high)])
  const { ticks, min, max } = niceTicks(yMin ?? Math.min(...all), yMax ?? Math.max(...all))
  const x = (i: number) => M.l + (i / 364) * PW
  const y = (v: number) => M.t + (1 - (v - min) / (max - min)) * PH
  const n = series[0]?.values.length ?? 0
  if (!n || !all.length) return null

  function hover(e: PointerEvent<HTMLDivElement>) {
    const r = e.currentTarget.getBoundingClientRect()
    const vx = ((e.clientX - r.left) / r.width) * W
    setIdx(Math.max(0, Math.min(364, Math.round(((vx - M.l) / PW) * 364))))
  }
  function key(e: KeyboardEvent<HTMLDivElement>) {
    const step = e.key === 'ArrowRight' ? 1 : e.key === 'ArrowLeft' ? -1 : e.key === 'PageDown' ? 30 : e.key === 'PageUp' ? -30 : 0
    if (!step) return
    e.preventDefault()
    setIdx((cur) => Math.max(0, Math.min(364, (cur ?? todayIndex ?? 0) + step)))
  }

  const monthly = DAYS_IN_MONTH.map((len, m) =>
    series.map((s) => {
      const part = nums(s.values.slice(MONTH_START[m], MONTH_START[m] + len))
      return part.length ? format(part.reduce((a, b) => a + b, 0) / part.length) : '–'
    }),
  )

  return (
    <div className="flex flex-col gap-3">
      <Legend items={series} />
      <div
        ref={box}
        className="relative touch-pan-y outline-offset-4"
        tabIndex={0}
        role="group"
        aria-label={title}
        aria-describedby={descId}
        onPointerMove={hover}
        onPointerLeave={() => setIdx(null)}
        onKeyDown={key}
        onFocus={() => setIdx((cur) => cur ?? todayIndex ?? 0)}
        onBlur={() => setIdx(null)}
      >
        <span id={descId} className="sr-only">
          {t('Use the left and right arrow keys to read values for each day.')}
        </span>
        <svg viewBox={`0 0 ${W} ${H}`} width={W} height={H} className="block" aria-hidden>
          <Axes d={d} ticks={ticks} y={y} format={axisFormat} months />
          {series.map(
            (s) =>
              s.low &&
              s.high && <path key={`${s.name}-band`} d={bandPath(s.low, s.high, x, y)} style={{ fill: s.color }} opacity={0.12} />,
          )}
          {todayIndex !== undefined && (
            <g>
              <line x1={x(todayIndex)} x2={x(todayIndex)} y1={M.t} y2={M.t + PH} className="stroke-muted" strokeWidth={1} strokeDasharray="2 3" />
              <text x={x(todayIndex)} y={M.t - 2} textAnchor="middle" className="fill-muted text-[11px]">
                {t('Today')}
              </text>
            </g>
          )}
          {series.map((s) => (
            <path key={s.name} d={linePath(s.values, x, y)} fill="none" strokeWidth={2} strokeLinecap="round" strokeLinejoin="round" style={{ stroke: s.color }} />
          ))}
          {idx !== null && (
            <g>
              <line x1={x(idx)} x2={x(idx)} y1={M.t} y2={M.t + PH} className="stroke-ink" strokeWidth={1} opacity={0.4} />
              {series.map((s) => {
                const v = s.values[idx]
                return v === null || v === undefined ? null : (
                  <circle key={s.name} cx={x(idx)} cy={y(v)} r={4} strokeWidth={2} className="stroke-surface" style={{ fill: s.color }} />
                )
              })}
            </g>
          )}
        </svg>
        {idx !== null && (
          <Tooltip
            d={d}
            at={idx / 364}
            title={dayLabel(idx)}
            rows={series.map((s) => ({
              name: s.low && s.high && s.low[idx] !== null && s.high[idx] !== null ? `${s.name} (${format(s.low[idx] as number)} to ${format(s.high[idx] as number)})` : s.name,
              color: s.color,
              value: s.values[idx] === null || s.values[idx] === undefined ? '–' : format(s.values[idx] as number),
            }))}
          />
        )}
      </div>
      <TableView head={[t('Month'), ...series.map((s) => s.name)]} rows={monthly.map((row, m) => [monthLong(m), ...row])} />
    </div>
  )
}

/** One column per month, for totals such as rainfall. */
export function MonthBars({
  title,
  values,
  color,
  format,
  axisFormat = format,
  highlight,
}: {
  title: string
  values: (number | null)[]
  color: string
  format: (v: number) => string
  axisFormat?: (v: number) => string
  /** Month index (0-11) to draw in the strong tone, e.g. the current month. */
  highlight?: number
}) {
  const [idx, setIdx] = useState<number | null>(null)
  const [box, d] = useDim()
  const { W, H, PW, PH } = d
  const present = nums(values)
  if (values.length !== 12 || !present.length) return null
  const { ticks, max } = niceTicks(0, Math.max(...present))
  const y = (v: number) => M.t + (1 - v / max) * PH
  const slot = PW / 12
  const bar = Math.min(24, slot - 8)
  const topMonth = values.indexOf(Math.max(...present)) // first month only when several tie

  return (
    <div className="flex flex-col gap-3">
      <div ref={box} className="relative">
        {/* Hover only: the table below gives keyboard and screen-reader access to every value. */}
        <svg viewBox={`0 0 ${W} ${H}`} width={W} height={H} className="block" role="img" aria-label={title}>
          <Axes d={d} ticks={ticks} y={y} format={axisFormat} months={false} />
          {values.map((v, m) => {
            const cx = M.l + slot * (m + 0.5)
            const h = v === null ? 0 : PH - (y(v) - M.t)
            const r = Math.min(4, h)
            return (
              <g key={m} onPointerEnter={() => setIdx(m)} onPointerLeave={() => setIdx(null)}>
                <rect x={cx - slot / 2} y={M.t} width={slot} height={PH + 24} fill="transparent" />
                {v !== null && h > 0 && (
                  <path
                    d={`M${cx - bar / 2} ${M.t + PH}V${y(v) + r}Q${cx - bar / 2} ${y(v)} ${cx - bar / 2 + r} ${y(v)}H${cx + bar / 2 - r}Q${cx + bar / 2} ${y(v)} ${cx + bar / 2} ${y(v) + r}V${M.t + PH}Z`}
                    style={{ fill: color }}
                    opacity={idx === null || idx === m ? (highlight === undefined || highlight === m ? 1 : 0.75) : 0.45}
                  />
                )}
                {v !== null && m === topMonth && idx === null && (
                  <text x={cx} y={y(v) - 6} textAnchor="middle" className="fill-ink text-[11px] font-bold">
                    {format(v)}
                  </text>
                )}
                <text x={cx} y={H - 8} textAnchor="middle" className="fill-muted text-[11px]">
                  {monthShort(m)}
                </text>
              </g>
            )
          })}
        </svg>
        {idx !== null && values[idx] !== null && (
          <Tooltip d={d} at={(idx + 0.5) / 12} title={monthLong(idx)} rows={[{ name: title, color, value: format(values[idx] as number) }]} />
        )}
      </div>
      <TableView head={[t('Month'), title]} rows={values.map((v, m) => [monthLong(m), v === null ? '–' : format(v)])} />
    </div>
  )
}

/** Day of the year (0-364) for a date, matching the engine's 365-day years. */
export function dayOfYear(d = new Date()): number {
  const i = MONTH_START[d.getMonth()] + d.getDate() - 1
  return Math.min(364, d.getMonth() === 1 && d.getDate() === 29 ? i - 1 : i)
}
