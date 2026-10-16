import { useEffect, useRef, useState, type ButtonHTMLAttributes } from 'react'
import { Calendar, ChevronLeft, ChevronRight } from 'lucide-react'
import { t } from '../../i18n'

const iso = (y: number, m: number, d: number) => `${y}-${String(m + 1).padStart(2, '0')}-${String(d).padStart(2, '0')}`
const parse = (s: string): [number, number, number] | null => {
  const m = /^(\d{4})-(\d{2})-(\d{2})$/.exec(s)
  return m ? [Number(m[1]), Number(m[2]) - 1, Number(m[3])] : null
}
const label = (s: string) => {
  const p = parse(s)
  return p ? new Date(p[0], p[1], p[2]).toLocaleDateString(undefined, { day: 'numeric', month: 'short', year: 'numeric' }) : ''
}

/** A date field in the app's own colours (the browser's date popup cannot be themed). Value is `YYYY-MM-DD` or ''. */
export default function DateField({
  value,
  onChange,
  required,
  className = '',
  ...rest
}: { value: string; onChange: (value: string) => void; required?: boolean; className?: string } & Omit<ButtonHTMLAttributes<HTMLButtonElement>, 'value' | 'onChange'>) {
  const [open, setOpen] = useState(false)
  const now = new Date()
  const [shown, setShown] = useState<[number, number]>(() => {
    const p = parse(value)
    return p ? [p[0], p[1]] : [now.getFullYear(), now.getMonth()]
  })
  const box = useRef<HTMLDivElement>(null)
  useEffect(() => {
    if (!open) return
    const close = (e: Event) => {
      if (e.type === 'keydown' ? (e as KeyboardEvent).key === 'Escape' : !box.current?.contains(e.target as Node)) setOpen(false)
    }
    document.addEventListener('pointerdown', close)
    document.addEventListener('keydown', close)
    return () => {
      document.removeEventListener('pointerdown', close)
      document.removeEventListener('keydown', close)
    }
  }, [open])

  const [y, m] = shown
  const lead = (new Date(y, m, 1).getDay() + 6) % 7 // weeks start on Monday
  const days = new Date(y, m + 1, 0).getDate()
  const step = (n: number) => setShown(([yy, mm]) => [yy + Math.floor((mm + n) / 12), (((mm + n) % 12) + 12) % 12])
  const today = iso(now.getFullYear(), now.getMonth(), now.getDate())
  const pick = (v: string) => {
    onChange(v)
    setOpen(false)
  }
  return (
    <div ref={box} className={`relative ${className}`}>
      <button
        type="button"
        {...rest}
        className="input flex w-full items-center justify-between gap-2 text-left"
        aria-haspopup="dialog"
        aria-expanded={open}
        onClick={() => setOpen(!open)}
      >
        <span className={value ? '' : 'text-muted'}>{label(value) || t('Choose a date')}</span>
        <Calendar className="size-4 shrink-0 text-muted" aria-hidden />
      </button>
      {open && (
        <div role="dialog" aria-label={t('Choose a date')} className="absolute left-0 z-30 mt-1 w-72 max-w-[calc(100vw-2rem)] rounded-2xl border border-line bg-surface p-3 shadow-lg">
          <div className="mb-2 flex items-center justify-between">
            <button type="button" className="btn-ghost" aria-label={t('Previous month')} onClick={() => step(-1)}>
              <ChevronLeft className="size-4" aria-hidden />
            </button>
            <span className="font-semibold">{new Date(y, m, 1).toLocaleDateString(undefined, { month: 'long', year: 'numeric' })}</span>
            <button type="button" className="btn-ghost" aria-label={t('Next month')} onClick={() => step(1)}>
              <ChevronRight className="size-4" aria-hidden />
            </button>
          </div>
          <div className="grid grid-cols-7 gap-1 text-center text-sm">
            {Array.from({ length: 7 }, (_, i) => (
              <span key={i} className="py-1 text-xs font-semibold text-muted">
                {new Date(2024, 0, 1 + i).toLocaleDateString(undefined, { weekday: 'narrow' })}
              </span>
            ))}
            {Array.from({ length: lead }, (_, i) => (
              <span key={`b${i}`} />
            ))}
            {Array.from({ length: days }, (_, i) => {
              const v = iso(y, m, i + 1)
              return (
                <button
                  key={v}
                  type="button"
                  aria-pressed={v === value}
                  onClick={() => pick(v)}
                  className={`min-h-9 rounded-lg ${v === value ? 'bg-leaf font-bold text-surface' : v === today ? 'border border-leaf' : 'hover:bg-sunken'}`}
                >
                  {i + 1}
                </button>
              )
            })}
          </div>
          <div className="mt-2 flex justify-between">
            <button type="button" className="btn-ghost" onClick={() => pick(today)}>
              {t('Today')}
            </button>
            {!required && value && (
              <button type="button" className="btn-ghost" onClick={() => pick('')}>
                {t('Clear')}
              </button>
            )}
          </div>
        </div>
      )}
    </div>
  )
}
