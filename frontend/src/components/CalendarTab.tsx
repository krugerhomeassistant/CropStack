import { useEffect, useState } from 'react'
import { ChevronLeft, ChevronRight } from 'lucide-react'
import { api, type CalendarEvent } from '../api'
import { t } from '../i18n'
import { Badge, ErrorMessage, IconButton, Section } from './ui'

const iso = (d: Date) => `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}-${String(d.getDate()).padStart(2, '0')}`
const KIND = { sow: 'Sow', set_out: 'Set out', harvest: 'Harvest' } as const
const DOT = { sow: 'bg-leaf', set_out: 'bg-muted', harvest: 'bg-harvest' } as const

/** A month of sowing, setting-out and harvest days; tap a day to see what is planned. */
export default function CalendarTab() {
  const today = iso(new Date())
  const [month, setMonth] = useState(() => new Date(new Date().getFullYear(), new Date().getMonth(), 1))
  const [events, setEvents] = useState<CalendarEvent[]>([])
  const [day, setDay] = useState(today)
  const [error, setError] = useState('')

  const last = new Date(month.getFullYear(), month.getMonth() + 1, 0)
  useEffect(() => {
    setError('')
    api.calendar(iso(month), iso(last)).then(setEvents, (e) => setError(e instanceof Error ? e.message : t('Failed to load')))
  }, [month])

  const lead = (month.getDay() + 6) % 7 // Monday first
  const cells = [...Array(lead).fill(null), ...Array.from({ length: last.getDate() }, (_, i) => i + 1)]
  const on = (d: string) => events.filter((e) => e.date === d)
  const step = (n: number) => setMonth(new Date(month.getFullYear(), month.getMonth() + n, 1))
  const monthName = month.toLocaleDateString(undefined, { month: 'long', year: 'numeric' })

  return (
    <Section
      title={monthName}
      action={
        <div className="flex">
          <IconButton icon={ChevronLeft} label={t('Previous month')} onClick={() => step(-1)} />
          <IconButton icon={ChevronRight} label={t('Next month')} onClick={() => step(1)} />
        </div>
      }
    >
      {error && <ErrorMessage>{error}</ErrorMessage>}
      <div className="grid grid-cols-7 gap-1 text-center text-xs text-muted" aria-hidden>
        {[1, 2, 3, 4, 5, 6, 0].map((d) => (
          <span key={d}>{new Date(2024, 0, 7 + d).toLocaleDateString(undefined, { weekday: 'narrow' })}</span>
        ))}
      </div>
      <div className="grid grid-cols-7 gap-1">
        {cells.map((n, i) => {
          if (!n) return <span key={`b${i}`} />
          const d = iso(new Date(month.getFullYear(), month.getMonth(), n))
          const kinds = [...new Set(on(d).map((e) => e.kind))]
          return (
            <button
              key={d}
              type="button"
              aria-label={`${n} ${monthName}${kinds.length ? `, ${on(d).length}` : ''}`}
              aria-pressed={d === day}
              onClick={() => setDay(d)}
              className={`flex min-h-12 flex-col items-center justify-center gap-1 rounded-[var(--radius-row)] text-sm ${
                d === day ? 'bg-leaf text-white' : d === today ? 'bg-sunken font-bold' : 'hover:bg-sunken'
              }`}
            >
              {n}
              <span className="flex h-1.5 gap-0.5">
                {kinds.map((k) => (
                  <span key={k} className={`size-1.5 rounded-full ${d === day ? 'bg-white' : DOT[k]}`} />
                ))}
              </span>
            </button>
          )
        })}
      </div>
      <div className="flex flex-col gap-2 border-t border-line pt-3">
        <h3 className="font-bold">{new Date(`${day}T00:00:00`).toLocaleDateString(undefined, { weekday: 'long', day: 'numeric', month: 'long' })}</h3>
        {on(day).length === 0 ? (
          <p className="text-sm text-muted">{t('Nothing planned.')}</p>
        ) : (
          <ul className="flex flex-col gap-2 text-sm">
            {on(day).map((e, i) => (
              <li key={i} className="flex items-center justify-between gap-3">
                <span className={e.done ? 'text-muted line-through' : ''}>{e.title}</span>
                <Badge tone={e.kind === 'harvest' ? 'marigold' : 'leaf'}>{t(KIND[e.kind])}</Badge>
              </li>
            ))}
          </ul>
        )}
      </div>
    </Section>
  )
}
