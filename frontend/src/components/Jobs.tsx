import { useEffect, useState } from 'react'
import { CalendarCheck, Check, ChevronDown } from 'lucide-react'
import { api, type Job, type TodayData } from '../api'
import { N_, t } from '../i18n'
import { useApp } from '../state'
import { Badge, Button, EmptyState, ErrorState, Section, Skeleton } from './ui'

const GROUP: Record<string, string> = {
  Protect: N_('Protect'),
  Plant: N_('Plant'),
  Water: N_('Water'),
  Feed: N_('Feed'),
  Harvest: N_('Harvest'),
  Animals: N_('Animals'),
  Check: N_('Check'),
  Maintain: N_('Maintain'),
}
const DONE: Record<Job['kind'], string> = { sow: N_('Mark sown'), set_out: N_('Mark set out'), harvest: N_('Mark harvest started'), frost: N_('Covered'), heat: N_('Done'), water: N_('Watered'), check: N_('Checked') }

const day = (iso: string) => new Date(`${iso}T00:00:00`).toLocaleDateString(undefined, { weekday: 'short', day: 'numeric', month: 'short' })

/** The two or three things worth seeing without opening the card. */
function brief(job: Job): string[] {
  const text = (label: string) => job.facts.find((f) => f.label === label)?.text
  const depth = text('Sow depth')
  const space = text('Space plants')?.split(',')[0]
  const roots = text('Roots reach')?.split(',')[0]
  return [depth && (depth.startsWith('barely') ? t('barely covered') : t('{depth} deep', { depth })), space, roots && t('roots {roots}', { roots })].filter((x): x is string => !!x)
}

function JobCard({ job, canEdit, onFinish, onDecline }: { job: Job; canEdit: boolean; onFinish: (id: number, s: 'done' | 'skipped') => void; onDecline: (plantingId: number) => void }) {
 const [sure, setSure] = useState(false)
 const declinable = canEdit && job.planting_id !== null && (job.kind === 'sow' || job.kind === 'set_out')
 const harvestLabel = job.purpose === 'companion' ? N_('Mark flowering started') : N_('Mark harvest started')
 const highlights = brief(job)
 return (
 <li className="rounded-[var(--radius-row)] border border-line bg-surface px-3 py-2.5">
 <div className="flex items-start gap-3">
 <div className="min-w-0 flex-1">
 <div className="flex items-center gap-2">
 <h4 className="truncate font-bold">{job.title}</h4>
 {job.overdue && <Badge tone="marigold">{t('Overdue')}</Badge>}
 </div>
 <p className="mt-0.5 text-sm text-muted">{job.reason}</p>
 {highlights.length > 0 && <p className="mt-1 text-xs font-semibold text-leaf">{highlights.join(' · ')}</p>}
 </div>
 {canEdit && <Button className="shrink-0" onClick={() => onFinish(job.id, 'done')}>
 <Check className="size-4" aria-hidden /> {t(job.kind === 'harvest' ? harvestLabel : DONE[job.kind])}
 </Button>}
 </div>
 {(job.facts.length > 0 || job.steps.length > 0 || job.watch.length > 0 || canEdit) && (
 <details className="group mt-1">
 <summary className="flex min-h-8 cursor-pointer list-none items-center gap-1 text-xs font-semibold text-leaf [&::-webkit-details-marker]:hidden">
 <ChevronDown className="size-4 transition-transform group-open:rotate-180" aria-hidden /> {t('Details')}
 </summary>
 <div className="border-t border-line pt-2 text-sm">
 {job.facts.length > 0 && <dl className="mb-3 grid grid-cols-[auto_1fr] gap-x-4 gap-y-1">{job.facts.map((f) => <div key={f.label} className="contents"><dt className="font-semibold text-muted">{t(f.label)}</dt><dd>{f.text}</dd></div>)}</dl>}
 {job.steps.length > 0 && <ol className="list-decimal space-y-1 pl-5">{job.steps.map((step) => <li key={step}>{step}</li>)}</ol>}
 {job.watch.length > 0 && <ul className="mt-2 space-y-2">{job.watch.map((w) => <li key={w.slug}><span className="font-semibold">{w.name}</span>{w.verdict && <span className="text-leaf"> · {t(w.verdict)}</span>}<p className="text-muted">{w.identify}</p><p>{w.action}</p></li>)}</ul>}
 <div className="mt-3 flex flex-wrap items-center gap-2">
 {canEdit && <Button variant="ghost" onClick={() => onFinish(job.id, 'skipped')}>{t('Skip')}</Button>}
 {declinable && !sure && <Button variant="ghost" onClick={() => setSure(true)}>{t('Decline')}</Button>}
 {declinable && sure && (
 <>
 <span className="text-sm text-muted">{t('Take this planting out of the plan?')}</span>
 <Button variant="secondary" onClick={() => onDecline(job.planting_id!)}>{t('Yes, remove it')}</Button>
 <Button variant="ghost" onClick={() => setSure(false)}>{t('Keep')}</Button>
 </>
 )}
 </div>
 </div>
 </details>
 )}
 </li>
 )
}

/** The household's jobs for today, grouped, and what is coming in the next two weeks. */
export default function Jobs() {
  const { user } = useApp()
  const [data, setData] = useState<TodayData | null>(null)
  const [error, setError] = useState<string | null>(null)
  const canEdit = user.role !== 'viewer'

  function load() {
    setError(null)
    api.today().then(setData, (e) => setError(e instanceof Error ? e.message : t('Failed to load')))
  }
  useEffect(load, [])

  function finish(id: number, status: 'done' | 'skipped') {
    api.finishJob(id, status).then(load, (e) => setError(e instanceof Error ? e.message : t('Failed to save')))
  }

  function decline(plantingId: number) {
    api.deletePlanting(plantingId).then(load, (e) => setError(e instanceof Error ? e.message : t('Failed to save')))
  }

  const title = t("Today's jobs")
  if (error)
    return (
      <Section title={title} className="lg:order-1">
        <ErrorState message={error} onRetry={load} />
      </Section>
    )
  if (!data) return <Skeleton className="h-48 lg:order-1" />

  const none = data.groups.length === 0
  return (
    <div className="flex flex-col gap-6 lg:order-1">
      <Section title={title} description={!none ? t('Small steps for the garden today. Open a job for full guidance.') : undefined}>
        {none ? (
          <EmptyState icon={CalendarCheck} title={t('Nothing to do today')}>
            {data.upcoming.length
              ? t('The next jobs are listed below.')
              : t('Add a planting from a crop page, and its jobs show up here when they are due.')}
          </EmptyState>
        ) : (
          data.groups.map(({ group, tasks }) => (
            <div key={group} className="flex flex-col gap-3">
              <h3 className="font-display text-lg font-bold">{t(GROUP[group] ?? group)}</h3>
              <ul className="flex flex-col gap-3">
                {tasks.map((job) => (
                  <JobCard key={job.id} job={job} canEdit={canEdit} onFinish={finish} onDecline={decline} />
                ))}
              </ul>
            </div>
          ))
        )}
      </Section>
      {data.upcoming.length > 0 && (
        <Section title={t('Coming up')} description={t('The next two weeks.')}>
          <ul className="flex flex-col divide-y divide-line">
            {data.upcoming.map((job) => (
              <li key={job.id} className="flex items-baseline justify-between gap-3 border-b border-line py-2 last:border-0 last:pb-0 first:pt-0">
                <span className="font-semibold">{job.title}</span>
                <span className="shrink-0 text-sm text-muted">{day(job.ideal)}</span>
              </li>
            ))}
          </ul>
        </Section>
      )}
    </div>
  )
}
