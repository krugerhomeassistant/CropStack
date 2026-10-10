import { useEffect, useState } from 'react'
import { api, type Bed, type Planting } from '../api'
import { t } from '../i18n'
import { useApp } from '../state'
import { Button, ErrorMessage, Field } from './ui'

const iso = (d: Date) => `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}-${String(d.getDate()).padStart(2, '0')}`

/** The next date on or after today that falls on "MM-DD". */
export function nextOccurrence(md: string, today = new Date()): string {
  const [m, d] = md.split('-').map(Number)
  const date = new Date(today.getFullYear(), m - 1, d)
  if (date < new Date(today.getFullYear(), today.getMonth(), today.getDate())) date.setFullYear(date.getFullYear() + 1)
  return iso(date)
}

/** Records a planting from a window: "Plant this" opens the form with the best date filled in. */
export default function PlantForm({
  crop,
  method,
  date,
  ageDays,
}: {
  crop: string
  method: 'direct' | 'transplant'
  /** Best sowing (direct) or set-out (transplant) day, as MM-DD. */
  date: string
  ageDays?: number
}) {
  const { user } = useApp()
  const [open, setOpen] = useState(false)
  const [when, setWhen] = useState(() => nextOccurrence(date))
  const [quantity, setQuantity] = useState('1')
  const [location, setLocation] = useState('')
  const [beds, setBeds] = useState<Bed[]>([])
  const [bedId, setBedId] = useState('')
  const [error, setError] = useState('')
  const [saved, setSaved] = useState<Planting | null>(null)

  useEffect(() => {
    if (open) api.beds().then(setBeds, () => setBeds([]))
  }, [open])

  if (user.role === 'viewer') return null
  if (saved) return <p className="text-sm font-semibold text-leaf">{t('Added to your plantings, in the Garden tab.')}</p>
  if (!open)
    return (
      <Button variant="secondary" className="self-start" onClick={() => setOpen(true)}>
        {t('Plant this')}
      </Button>
    )

  const transplant = method === 'transplant'
  function save() {
    setError('')
    const day = new Date(`${when}T00:00:00`)
    const sow = transplant ? iso(new Date(day.getFullYear(), day.getMonth(), day.getDate() - (ageDays ?? 0))) : when
    api
      .addPlanting({
        crop,
        method,
        start_date: sow,
        set_out_date: transplant ? when : null,
        quantity: Math.max(1, Number(quantity) || 1),
        location: bedId ? '' : location,
        bed_id: bedId ? Number(bedId) : null,
        notes: '',
      })
      .then(setSaved, (e) => setError(e instanceof Error ? e.message : t('Failed to save')))
  }

  return (
    <form
      className="flex flex-col gap-3 rounded-[var(--radius-row)] bg-sunken p-4"
      onSubmit={(e) => {
        e.preventDefault()
        save()
      }}
    >
      <Field label={transplant ? t('Set-out date') : t('Sowing date')}>
        <input className="input" type="date" required value={when} onChange={(e) => setWhen(e.target.value)} />
      </Field>
      {transplant && ageDays ? (
        <p className="text-sm text-muted">{t('Sow indoors {days} days before.', { days: ageDays })}</p>
      ) : null}
      <Field label={t('How many')}>
        <input className="input" type="number" min={1} value={quantity} onChange={(e) => setQuantity(e.target.value)} />
      </Field>
      {beds.length > 0 && (
        <Field label={t('Bed')}>
          <select className="input" value={bedId} onChange={(e) => setBedId(e.target.value)}>
            <option value="">{t('Somewhere else')}</option>
            {beds.map((b) => (
              <option key={b.id} value={b.id}>
                {b.name}
              </option>
            ))}
          </select>
        </Field>
      )}
      {!bedId && (
        <Field label={t('Where')} hint={t('A bed, a row or a pot.')}>
          <input className="input" maxLength={120} value={location} onChange={(e) => setLocation(e.target.value)} />
        </Field>
      )}
      {error && <ErrorMessage>{error}</ErrorMessage>}
      <div className="flex gap-2">
        <Button type="submit">{t('Save planting')}</Button>
        <Button variant="ghost" onClick={() => setOpen(false)}>
          {t('Cancel')}
        </Button>
      </div>
    </form>
  )
}
