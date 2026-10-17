import { useEffect, useState } from 'react'
import { CalendarRange, X } from 'lucide-react'
import { api, type Coverage, type PlanDiff, type PlanItem, type Planting } from '../api'
import { t } from '../i18n'
import { useApp } from '../state'
import CoverageCard, { PeopleStepper } from './CoverageCard'
import { CropIcon } from './CropIcon'
import { Button, EmptyState, ErrorMessage, IconButton, Section } from './ui'

const day = (s: string) => new Date(`${s}T00:00:00`).toLocaleDateString(undefined, { day: 'numeric', month: 'short' })
const month = (s: string) => new Date(`${s}T00:00:00`).toLocaleDateString(undefined, { month: 'long', year: 'numeric' })
const planted = (i: PlanItem) => i.set_out_date ?? i.start_date

/** A year of plantings drafted for the beds. Review it by month, leave out what you do not want, then use it. */
export default function YearPlan({ hasBeds, scheduled, plan, setPlan, onUsed, onCleared }: { hasBeds: boolean; scheduled: number; plan: PlanItem[]; setPlan: (p: PlanItem[]) => void; onUsed: () => void; onCleared: () => void }) {
  const canEdit = useApp().user.role !== 'viewer'
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState('')
  const [sure, setSure] = useState(false)
  const [people, setPeople] = useState<number | null>(null)
  const [coverage, setCoverage] = useState<Coverage | null>(null)
  const [skipped, setSkipped] = useState<string[]>([])
 const [planCount, setPlanCount] = useState(0)
 const [diff, setDiff] = useState<PlanDiff | null>(null)
 const [confirmReplan, setConfirmReplan] = useState(false)
  const canChange = useApp().user.role === 'owner'
  const [saved, setSaved] = useState<Planting[]>([])
  const [names, setNames] = useState<Record<string, string>>({})
  const [seeds, setSeeds] = useState<string[]>([])
  const [buy, setBuy] = useState<{ crop: string; name: string }[]>([])
  // The plan you have used stays here: it is the saved plantings the year plan made, whatever tab you are on.
  useEffect(() => {
    api.crops().then((cs) => setNames(Object.fromEntries(cs.map((c) => [c.slug, c.names.en?.[0] ?? c.slug]))), () => {})
  }, [])
  useEffect(() => {
    api.plantings().then((ps) => setSaved(ps.filter((p) => p.source === 'plan' && !['finished', 'failed'].includes(p.status))), () => {})
  }, [scheduled, busy])
  const fail = (e: unknown) => {
    setBusy(false)
    setError(e instanceof Error ? e.message : t('Failed to save'))
  }
  useEffect(() => {
    api.seeds().then(setSeeds, () => {})
  }, [])
  const saveSeeds = (next: string[]) => {
    setSeeds(next)
    api.setSeeds(next).then(setSeeds, fail)
  }
  useEffect(() => {
    api.householdSettings().then((s) => setPeople(s.people), fail)
  }, [])
  const draft = () => {
  if (scheduled > 0 && !confirmReplan) {
  setConfirmReplan(true)
  return
  }
  setConfirmReplan(false)
  setBusy(true)
  setError('')
    api.yearPlan().then((r) => {
      setPlan(r.items)
      setCoverage(r.coverage ?? null)
      setPeople(r.people)
      setSkipped(r.skipped_no_yield ?? [])
      setBuy(r.buy ?? [])
 setPlanCount(r.plan_count ?? r.scheduled)
 if (scheduled > 0) {
 const proposed = r.items.map((i) => ({ crop: i.crop, method: i.method, start_date: i.start_date, set_out_date: i.set_out_date, bed_id: i.bed_id, cells: i.cells, location: '', notes: '' }))
 api.previewPlan(proposed).then(setDiff, fail)
 } else {
 setDiff(null)
 }
 setBusy(false)
      if (r.items.length === 0) setError(t('Nothing fits right now. Add beds or free up cells, then draft again.'))
    }, fail)
  }
  /** The plan is sized for the head count, so once a draft exists a change of people drafts again. */
  const changePeople = (n: number) => {
    setBusy(true)
    setError('')
    api.saveHouseholdSettings({ people: n }).then(() => {
      setPeople(n)
      setBusy(false)
      if (coverage) draft()
    }, fail)
  }
  const use = () => {
    setBusy(true)
    api
      .acceptPlan(plan.map((i) => ({ crop: i.crop, method: i.method, start_date: i.start_date, set_out_date: i.set_out_date, bed_id: i.bed_id, cells: i.cells, location: '', notes: '' })))
      .then(() => {
        setBusy(false)
        setPlan([])
        onUsed()
      }, fail)
  }
  const clear = () => {
    setBusy(true)
    api.clearPlan().then(() => {
      setBusy(false)
      setSure(false)
      setPlan([])
      onCleared()
    }, fail)
  }
  const months = [...new Set(plan.map((i) => month(planted(i))))]
  const when = (p: Planting) => p.set_out_date ?? p.start_date
  const savedSorted = [...saved].sort((a, b) => when(a).localeCompare(when(b)))
  const savedMonths = [...new Set(savedSorted.map((p) => month(when(p))))]
  const totals = new Map<string, number>()
  for (const p of saved) totals.set(p.crop, (totals.get(p.crop) ?? 0) + p.quantity)
  return (
    <Section
      title={t('Year plan')}
      description={t('A draft of what to plant where over the next 12 months, from your climate and what already grows in your beds.')}
    >
      {people !== null && (coverage ? <CoverageCard coverage={coverage} people={people} canChange={canChange} onPeople={changePeople} /> : <PeopleStepper people={people} canChange={canChange} onPeople={changePeople} />)}
      {canEdit && hasBeds && (
        <div className="flex flex-col gap-2" aria-label={t('Seeds I have')}>
          <p className="text-sm font-semibold">{t('Seeds I have')}</p>
          <p className="text-sm text-muted">{t('Pick the seed you already have. The plan leans on it, then lists the seed still to buy.')}</p>
          <ul className="flex flex-wrap gap-2">
            {seeds.map((s) => (
              <li key={s} className="flex items-center gap-1 rounded-full border border-line px-3 py-1 text-sm">
                <span aria-hidden><CropIcon crop={s} /></span> {names[s] ?? s}
                <IconButton icon={X} label={t('Remove {crop}', { crop: names[s] ?? s })} onClick={() => saveSeeds(seeds.filter((x) => x !== s))} />
              </li>
            ))}
          </ul>
          <select className="input w-auto max-w-full" aria-label={t('Add seed')} value="" onChange={(e) => e.target.value && saveSeeds([...seeds, e.target.value])}>
            <option value="">{t('Add a seed…')}</option>
            {Object.entries(names)
              .filter(([slug]) => !seeds.includes(slug))
              .sort((a, b) => a[1].localeCompare(b[1]))
              .map(([slug, name]) => (
                <option key={slug} value={slug}>{name}</option>
              ))}
          </select>
        </div>
      )}
      {canEdit && hasBeds && (
 <div>
 {!confirmReplan ? (
 <Button variant={plan.length ? 'secondary' : 'primary'} onClick={draft} disabled={busy}>{busy ? t('Drafting…') : plan.length ? t('Draft again') : t('Draft a year plan')}</Button>
 ) : (
 <div className="flex flex-wrap items-center gap-2 rounded-[var(--radius-row)] border border-harvest/50 bg-harvest/10 p-3">
 <span className="text-sm font-semibold text-harvest">{t('This replaces {n} plan plantings. Hand-planted crops stay.', { n: planCount })}</span>
 <Button variant="secondary" onClick={() => draft()} disabled={busy}>{t('Continue draft')}</Button>
 <Button variant="ghost" onClick={() => setConfirmReplan(false)}>{t('Keep current plan')}</Button>
 </div>
 )}
 </div>
 )}

      {canEdit && planCount > 0 && (
        <div className="flex flex-wrap items-center gap-2 text-sm">
          <span className="text-muted">{t('{n} plantings from an earlier plan are still to do. Drafting again replaces them; what you have sown or planted stays.', { n: planCount })}</span>
          {sure ? (
            <>
              <Button variant="secondary" onClick={clear} disabled={busy}>{t('Yes, clear {n}', { n: planCount })}</Button>
              <Button variant="ghost" onClick={() => setSure(false)}>{t('Keep')}</Button>
            </>
          ) : (
            <Button variant="ghost" onClick={() => setSure(true)} disabled={busy}>{t('Clear plan')}</Button>
          )}
        </div>
      )}
      {!hasBeds && <EmptyState icon={CalendarRange} title={t('Draw your beds first')}>{t('The plan fills the beds you draw on the Plan tab.')}</EmptyState>}
      {error && <ErrorMessage>{error}</ErrorMessage>}
 {diff && (diff.added > 0 || diff.removed > 0 || diff.moved > 0) && (
 <p className="rounded-[var(--radius-row)] border border-line p-3 text-sm">
 {t('Draft changes: {added} added, {removed} removed, {moved} moved. Review the list below before using it; nothing has changed yet.', { added: diff.added, removed: diff.removed, moved: diff.moved })}
 </p>
 )}
      {skipped.length > 0 && <p className="text-sm text-muted">{t('Left out, no yield data yet: {crops}', { crops: skipped.join(', ') })}</p>}
      {months.map((m) => (
        <div key={m} className="flex flex-col gap-1">
          <p className="text-sm font-semibold">{m}</p>
          <ul className="flex flex-col divide-y divide-line">
            {plan
              .filter((i) => month(planted(i)) === m)
              .map((i) => (
                <li key={`${i.crop}${i.bed_id}${planted(i)}`} className="flex items-center justify-between gap-3 py-2">
                  <div className="min-w-0">
                    <p className="font-bold">
                      <CropIcon crop={i.crop} /> {i.name} <span className="font-normal text-muted">· {i.bed}</span>
                    </p>
                    <p className="text-sm text-muted">
                      {i.method === 'transplant' ? t('Set out') : t('Sow')} {day(planted(i))} · {i.companion_for?.length ? t('in flower {from} to {to}', { from: day(i.harvest_from), to: day(i.harvest_to) }) : t('harvest {from} to {to}', { from: day(i.harvest_from), to: day(i.harvest_to) })} · {i.companion_for?.length ? t('{n} cells', { n: i.cells.length }) : t('{n} plants on {cells} cells', { n: i.plants, cells: i.cells.length })}
                    </p>
                    {i.companion_for?.length ? (
                      <p className="text-sm text-muted">{t('Companion flower for {crops}', { crops: i.companion_for.join(', ') })}</p>
                    ) : i.pairs_with?.length || i.flowers?.length || i.flower_hints?.length ? (
                      <p className="text-sm text-muted">
                        {[
                          i.pairs_with?.length ? t('Grows beside {crops}', { crops: i.pairs_with.join(', ') }) : '',
                          i.flowers?.length ? t('With {flowers} beside it', { flowers: i.flowers.join(', ') }) : '',
                          !i.flowers?.length && i.flower_hints?.length ? t('Traditionally grown with {flowers}', { flowers: i.flower_hints.join(', ') }) : '',
                        ]
                          .filter(Boolean)
                          .join(' · ')}
                      </p>
                    ) : null}
                  </div>
                  <IconButton icon={X} label={t('Leave out {crop}', { crop: i.name })} onClick={() => setPlan(plan.filter((x) => x !== i))} />
                </li>
              ))}
          </ul>
        </div>
      ))}
      {plan.length > 0 && canEdit && (
        <div className="flex flex-wrap items-center gap-2">
          <Button onClick={use} disabled={busy}>
            {t('Use this plan ({n} plantings)', { n: plan.length })}
          </Button>
          <Button variant="ghost" onClick={() => setPlan([])}>
            {t('Discard')}
          </Button>
        </div>
      )}
      {plan.length > 0 && buy.length > 0 && (
        <div className="flex flex-col gap-1" aria-label={t('Seeds to buy')}>
          <p className="text-sm font-semibold">{t('Seeds to buy')}</p>
          <ul className="flex flex-wrap gap-x-4 gap-y-0.5 text-sm">
            {buy.filter((b) => plan.some((i) => i.crop === b.crop)).map((b) => (
              <li key={b.crop}>
                <span aria-hidden><CropIcon crop={b.crop} /></span> {b.name}
              </li>
            ))}
          </ul>
        </div>
      )}
      {plan.length > 0 && <p className="text-xs text-muted">{t('The Plan tab shows these as dashed cells in each bed. Nothing is saved until you use the plan; after that, every planting can still be changed.')}</p>}
      {saved.length > 0 && (
        <div className="flex flex-col gap-3 border-t border-line pt-4" aria-label={t('Your plan')}>
          <div>
            <h3 className="font-bold">{t('Your plan')}</h3>
            <p className="text-sm text-muted">{t('{n} plantings are saved from the year plan. They show faint on the Plan tab until their day, and as jobs on Today and the Calendar.', { n: saved.length })}</p>
          </div>
          <ul className="flex flex-wrap gap-x-4 gap-y-0.5 text-sm" aria-label={t('What is planned')}>
            {[...totals].sort((a, b) => (names[a[0]] ?? a[0]).localeCompare(names[b[0]] ?? b[0])).map(([crop, n]) => (
              <li key={crop}>
                <span aria-hidden><CropIcon crop={crop} /></span> <span className="font-semibold">{n}× {names[crop] ?? crop}</span>
              </li>
            ))}
          </ul>
          {savedMonths.map((m) => (
            <div key={m} className="flex flex-col gap-1">
              <p className="text-sm font-semibold">{m}</p>
              <ul className="flex flex-col divide-y divide-line">
                {savedSorted
                  .filter((p) => month(when(p)) === m)
                  .map((p) => (
                    <li key={p.id} className="py-2">
                      <p className="font-bold">
                        <CropIcon crop={p.crop} /> {names[p.crop] ?? p.crop} <span className="font-normal text-muted">· {p.location}</span>
                      </p>
                      <p className="text-sm text-muted">
                        {p.status === 'planned' ? (p.method === 'transplant' ? t('Set out') : t('Sow')) : t('Started')} {day(when(p))} · {p.harvest_from && p.harvest_to ? `${p.purpose === 'companion' ? t('in flower {from} to {to}', { from: day(p.harvest_from), to: day(p.harvest_to) }) : t('harvest {from} to {to}', { from: day(p.harvest_from), to: day(p.harvest_to) })} · ` : ''}{t('{n} plants on {cells} cells', { n: p.quantity, cells: p.cells.length })}
                      </p>
                    </li>
                  ))}
              </ul>
            </div>
          ))}
        </div>
      )}
    </Section>
  )
}
