import { useEffect, useState } from 'react'
import { Egg } from 'lucide-react'
import { Link } from 'react-router'
import { api, type Bed, type Flock } from '../api'
import hen from '../icons/animals/hen.svg'
import { Button, EmptyState, ErrorMessage, ErrorState, Field, PageHeader, Section, Sheet, Skeleton } from '../components/ui'
import DateField from '../components/ui/DateField'
import { t } from '../i18n'
import { useApp } from '../state'

const today = () => new Date().toLocaleDateString('sv')
const Hen = () => <img src={hen} alt="" className="inline-block size-6 align-[-0.3em]" />

function AddForm({ coops, onSaved }: { coops: Bed[]; onSaved: () => void }) {
  const [name, setName] = useState(t('Hens'))
  const [breed, setBreed] = useState('')
  const [count, setCount] = useState('4')
  const [gotOn, setGotOn] = useState(today())
  const [coop, setCoop] = useState('')
  const [error, setError] = useState('')
  return (
    <form
      className="flex flex-col gap-3"
      onSubmit={(e) => {
        e.preventDefault()
        api
          .addFlock({ name: name.trim(), breed: breed.trim(), count: Number(count), got_on: gotOn, coop_id: coop ? Number(coop) : null, notes: '' })
          .then(onSaved, (err) => setError(err instanceof Error ? err.message : t('Failed to save')))
      }}
    >
      <Field label={t('Name')}>
        <input className="input" required maxLength={60} value={name} onChange={(e) => setName(e.target.value)} />
      </Field>
      <Field label={t('Breed (optional)')}>
        <input className="input" maxLength={60} value={breed} onChange={(e) => setBreed(e.target.value)} placeholder={t('Rhode Island Red')} />
      </Field>
      <div className="flex gap-2">
        <Field label={t('Hens')}>
          <input className="input w-24" type="number" min={1} max={10000} required value={count} onChange={(e) => setCount(e.target.value)} />
        </Field>
        <Field label={t('Got them on')}>
          <DateField required value={gotOn} onChange={setGotOn} />
        </Field>
      </div>
      <Field label={t('Coop')} hint={coops.length === 0 ? t('Draw a coop on the Plan tab to put them in it.') : undefined}>
        <select className="input" value={coop} onChange={(e) => setCoop(e.target.value)}>
          <option value="">{t('No coop yet')}</option>
          {coops.map((c) => (
            <option key={c.id} value={c.id}>
              {c.name}
            </option>
          ))}
        </select>
      </Field>
      {error && <ErrorMessage>{error}</ErrorMessage>}
      <Button type="submit">{t('Add flock')}</Button>
    </form>
  )
}

function FlockCard({ flock, canEdit, onChange, fail }: { flock: Flock; canEdit: boolean; onChange: () => void; fail: (e: unknown) => void }) {
  const [eggs, setEggs] = useState(flock.eggs_today === null ? '' : String(flock.eggs_today))
  const tight = flock.coop_m2 !== null && flock.coop_m2 < flock.wanted_m2
  return (
    <Section title={flock.name} description={`${flock.count} ${t('hens')}${flock.breed ? ` · ${flock.breed}` : ''}${flock.coop ? ` · ${flock.coop}` : ''}`}>
      <p className="text-sm">
        <Hen /> {t('{n} eggs this week', { n: flock.eggs_week })} · {t('{n} per hen a day', { n: flock.per_hen_day })}
      </p>
      {tight && (
        <p className="text-sm text-muted">{t('{count} hens like about {want} m² between coop and run; {coop} is {have} m². A rule of thumb, not a limit.', { count: flock.count, want: flock.wanted_m2, coop: flock.coop ?? '', have: flock.coop_m2 ?? 0 })}</p>
      )}
      {canEdit && (
        <form
          className="flex items-end gap-2"
          onSubmit={(e) => {
            e.preventDefault()
            api.logEggs(flock.id, today(), Number(eggs)).then(onChange, fail)
          }}
        >
          <Field label={t('Eggs today')}>
            <input className="input w-24" type="number" min={0} required value={eggs} onChange={(e) => setEggs(e.target.value)} />
          </Field>
          <Button type="submit" variant="secondary">{t('Save eggs')}</Button>
          <Button type="button" variant="ghost" onClick={() => api.updateFlock(flock.id, { count: Math.max(1, flock.count - 1) }).then(onChange, fail)}>{t('One fewer hen')}</Button>
        </form>
      )}
    </Section>
  )
}

/** Hens (more animals later): where they live, how many, and the eggs they lay. */
export default function Animals() {
  const canEdit = useApp().user.role !== 'viewer'
  const [flocks, setFlocks] = useState<Flock[] | null>(null)
  const [coops, setCoops] = useState<Bed[]>([])
  const [error, setError] = useState('')
  const [adding, setAdding] = useState(false)
  const load = () =>
    Promise.all([api.flocks(), api.beds()]).then(
      ([f, b]) => {
        setFlocks(f)
        setCoops(b.filter((x) => x.kind === 'coop'))
      },
      (e) => setError(e instanceof Error ? e.message : t('Failed to load')),
    )
  useEffect(() => {
    load()
  }, [])
  const fail = (e: unknown) => setError(e instanceof Error ? e.message : t('Failed to save'))
  if (error && !flocks) return <ErrorState message={error} onRetry={load} />
  return (
    <>
      <PageHeader title={t('Animals')} subtitle={t('Hens, their coop and their eggs')} />
      {canEdit && <div><Button onClick={() => setAdding(true)}>{t('Add hens')}</Button></div>}
      {error && <ErrorMessage>{error}</ErrorMessage>}
      {!flocks && <Skeleton className="h-40" />}
      {flocks?.length === 0 && (
        <Section>
          <EmptyState icon={Egg} title={t('No animals yet')}>
            {t('Add your hens, and draw a coop and run on the Plan tab so they have a place on the plot.')} <Link to="/garden" className="font-semibold underline">{t('Open the plan')}</Link>
          </EmptyState>
        </Section>
      )}
      {flocks?.map((f) => <FlockCard key={f.id} flock={f} canEdit={canEdit} onChange={load} fail={fail} />)}
      <Sheet title={t('Add hens')} open={adding} onClose={() => setAdding(false)}>
        <AddForm coops={coops} onSaved={() => { setAdding(false); load() }} />
      </Sheet>
    </>
  )
}
