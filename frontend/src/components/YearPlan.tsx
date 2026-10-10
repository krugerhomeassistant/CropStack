import { useState } from 'react'
import { CalendarRange, X } from 'lucide-react'
import { api, type PlanItem } from '../api'
import { t } from '../i18n'
import { useApp } from '../state'
import { cropIcon } from './cropIcon'
import { Button, EmptyState, ErrorMessage, IconButton, Section } from './ui'

const day = (s: string) => new Date(`${s}T00:00:00`).toLocaleDateString(undefined, { day: 'numeric', month: 'short' })
const month = (s: string) => new Date(`${s}T00:00:00`).toLocaleDateString(undefined, { month: 'long', year: 'numeric' })
const planted = (i: PlanItem) => i.set_out_date ?? i.start_date

/** A year of plantings drafted for the beds. Review it by month, leave out what you do not want, then use it. */
export default function YearPlan({ hasBeds, plan, setPlan, onUsed }: { hasBeds: boolean; plan: PlanItem[]; setPlan: (p: PlanItem[]) => void; onUsed: () => void }) {
  const canEdit = useApp().user.role !== 'viewer'
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState('')
  const fail = (e: unknown) => {
    setBusy(false)
    setError(e instanceof Error ? e.message : t('Failed to save'))
  }
  const draft = () => {
    setBusy(true)
    setError('')
    api.yearPlan().then((r) => {
      setPlan(r.items)
      setBusy(false)
      if (r.items.length === 0) setError(t('Nothing fits right now. Add beds or free up cells, then draft again.'))
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
  const months = [...new Set(plan.map((i) => month(planted(i))))]
  return (
    <Section
      title={t('Year plan')}
      description={t('A draft of what to plant where over the next 12 months, from your climate and what already grows in your beds.')}
    >
      {canEdit && hasBeds && (
        <div>
          <Button variant={plan.length ? 'secondary' : 'primary'} onClick={draft} disabled={busy}>
            {busy ? t('Drafting…') : plan.length ? t('Draft again') : t('Draft a year plan')}
          </Button>
        </div>
      )}
      {!hasBeds && <EmptyState icon={CalendarRange} title={t('Draw your beds first')}>{t('The plan fills the beds you draw on the Plan tab.')}</EmptyState>}
      {error && <ErrorMessage>{error}</ErrorMessage>}
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
                      {cropIcon(i.crop)} {i.name} <span className="font-normal text-muted">· {i.bed}</span>
                    </p>
                    <p className="text-sm text-muted">
                      {i.method === 'transplant' ? t('Set out') : t('Sow')} {day(planted(i))} · {t('harvest {from} to {to}', { from: day(i.harvest_from), to: day(i.harvest_to) })} · {t('{n} cells', { n: i.cells.length })}
                    </p>
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
      {plan.length > 0 && <p className="text-xs text-muted">{t('The Plan tab shows these as dashed cells in each bed. Nothing is saved until you use the plan; after that, every planting can still be changed.')}</p>}
    </Section>
  )
}
