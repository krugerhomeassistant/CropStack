import { useEffect, useState } from 'react'
import { Package } from 'lucide-react'
import { api, type PantryIn, type PantryItem, type PantryMethod } from '../api'
import { Button, EmptyState, ErrorMessage, ErrorState, Field, PageHeader, Section, Sheet, Skeleton } from '../components/ui'
import { t } from '../i18n'
import { useApp } from '../state'

const METHODS: { value: PantryMethod; label: string; icon: string; hint: string }[] = [
  { value: 'canned', label: 'Canned or jarred', icon: '🥫', hint: 'Best within about a year' },
  { value: 'frozen', label: 'Frozen', icon: '❄️', hint: 'Best within about nine months' },
  { value: 'dried', label: 'Dried', icon: '☀️', hint: 'Best within about a year' },
  { value: 'fermented', label: 'Fermented or pickled', icon: '🫙', hint: 'Best within about six months' },
  { value: 'cellar', label: 'Root cellar or crate', icon: '🧺', hint: 'Check after about three months' },
  { value: 'fresh', label: 'Fresh', icon: '🥗', hint: 'A week or so' },
]
const UNITS: PantryIn['unit'][] = ['jars', 'bags', 'kg', 'g', 'litres', 'count']
const day = (s: string) => new Date(`${s}T00:00:00`).toLocaleDateString(undefined, { day: 'numeric', month: 'short', year: 'numeric' })
const today = () => new Date().toLocaleDateString('sv')

function AddForm({ onSaved }: { onSaved: () => void }) {
  const [name, setName] = useState('')
  const [method, setMethod] = useState<PantryMethod>('canned')
  const [quantity, setQuantity] = useState('1')
  const [unit, setUnit] = useState<PantryIn['unit']>('jars')
  const [madeOn, setMadeOn] = useState(today())
  const [best, setBest] = useState('')
  const [location, setLocation] = useState('')
  const [error, setError] = useState('')
  return (
    <form
      className="flex flex-col gap-3"
      onSubmit={(e) => {
        e.preventDefault()
        api
          .addPantry({ name: name.trim(), method, quantity: Number(quantity), unit, made_on: madeOn, best_before: best || null, location: location.trim(), notes: '' })
          .then(onSaved, (err) => setError(err instanceof Error ? err.message : t('Failed to save')))
      }}
    >
      <Field label={t('What is it?')}>
        <input className="input" required maxLength={80} value={name} onChange={(e) => setName(e.target.value)} placeholder={t('Tomato sauce')} />
      </Field>
      <Field label={t('How is it kept?')} hint={t(METHODS.find((m) => m.value === method)!.hint)}>
        <select className="input" value={method} onChange={(e) => setMethod(e.target.value as PantryMethod)}>
          {METHODS.map((m) => (
            <option key={m.value} value={m.value}>
              {m.icon} {t(m.label)}
            </option>
          ))}
        </select>
      </Field>
      <div className="flex gap-2">
        <Field label={t('Amount')}>
          <input className="input w-24" type="number" min="0.1" step="any" required value={quantity} onChange={(e) => setQuantity(e.target.value)} />
        </Field>
        <Field label={t('Unit')}>
          <select className="input" value={unit} onChange={(e) => setUnit(e.target.value as PantryIn['unit'])}>
            {UNITS.map((u) => (
              <option key={u} value={u}>
                {t(u)}
              </option>
            ))}
          </select>
        </Field>
      </div>
      <Field label={t('Put by on')}>
        <input className="input" type="date" required value={madeOn} onChange={(e) => setMadeOn(e.target.value)} />
      </Field>
      <Field label={t('Use by (optional)')} hint={t('Left blank, it is worked out from how it is kept.')}>
        <input className="input" type="date" value={best} onChange={(e) => setBest(e.target.value)} />
      </Field>
      <Field label={t('Where is it?')}>
        <input className="input" maxLength={80} value={location} onChange={(e) => setLocation(e.target.value)} placeholder={t('Pantry shelf 2')} />
      </Field>
      {error && <ErrorMessage>{error}</ErrorMessage>}
      <Button type="submit">{t('Add to pantry')}</Button>
    </form>
  )
}

function Row({ item, canEdit, onChange, fail }: { item: PantryItem; canEdit: boolean; onChange: () => void; fail: (e: unknown) => void }) {
  const m = METHODS.find((x) => x.value === item.method)!
  const when = item.best_before ? (item.state === 'past' ? t('Past its date ({date})', { date: day(item.best_before) }) : t('Use by {date}', { date: day(item.best_before) })) : t('No date')
  return (
    <li className="flex items-center justify-between gap-3 py-3 first:pt-0 last:pb-0">
      <div className="min-w-0">
        <p className="font-bold">
          <span aria-hidden>{m.icon}</span> {item.name}
        </p>
        <p className={`text-sm ${item.state === 'ok' ? 'text-muted' : item.state === 'soon' ? 'font-semibold text-harvest' : 'font-semibold text-danger'}`}>
          {item.quantity} {t(item.unit)} · {when}
          {item.location && ` · ${item.location}`}
        </p>
      </div>
      {canEdit && (
        <div className="flex shrink-0 gap-1">
          <Button
            variant="secondary"
            onClick={() => (item.quantity <= 1 ? api.deletePantry(item.id) : api.updatePantry(item.id, { quantity: item.quantity - 1 })).then(onChange, fail)}
            aria-label={t('Use one {name}', { name: item.name })}
          >
            {t('Use one')}
          </Button>
        </div>
      )}
    </li>
  )
}

/** Food that has been put by: what is there, where, and what to use first. */
export default function Pantry() {
  const canEdit = useApp().user.role !== 'viewer'
  const [items, setItems] = useState<PantryItem[] | null>(null)
  const [error, setError] = useState('')
  const [adding, setAdding] = useState(false)
  const load = () => api.pantry().then(setItems, (e) => setError(e instanceof Error ? e.message : t('Failed to load')))
  useEffect(() => {
    load()
  }, [])
  const fail = (e: unknown) => setError(e instanceof Error ? e.message : t('Failed to save'))
  if (error && !items) return <ErrorState message={error} onRetry={load} />
  const first = items?.filter((i) => i.state !== 'ok') ?? []
  const rest = items?.filter((i) => i.state === 'ok') ?? []
  return (
    <>
      <PageHeader title={t('Pantry')} subtitle={t('Put by, stored and preserved food')} />
      {canEdit && (
        <div>
          <Button onClick={() => setAdding(true)}>{t('Add food')}</Button>
        </div>
      )}
      {error && <ErrorMessage>{error}</ErrorMessage>}
      {!items && <Skeleton className="h-40" />}
      {items && items.length === 0 && (
        <Section>
          <EmptyState icon={Package} title={t('Nothing put by yet')}>
            {t('Add jars, bags and crates as you preserve the harvest, and this page will say what to use first.')}
          </EmptyState>
        </Section>
      )}
      {first.length > 0 && (
        <Section title={t('Use first')} description={t('Due within a month, or past its date.')}>
          <ul className="flex flex-col divide-y divide-line">
            {first.map((i) => (
              <Row key={i.id} item={i} canEdit={canEdit} onChange={load} fail={fail} />
            ))}
          </ul>
        </Section>
      )}
      {rest.length > 0 && (
        <Section title={t('In store')}>
          <ul className="flex flex-col divide-y divide-line">
            {rest.map((i) => (
              <Row key={i.id} item={i} canEdit={canEdit} onChange={load} fail={fail} />
            ))}
          </ul>
        </Section>
      )}
      <Sheet title={t('Add food')} open={adding} onClose={() => setAdding(false)}>
        <AddForm
          onSaved={() => {
            setAdding(false)
            load()
          }}
        />
      </Sheet>
    </>
  )
}
