import { useEffect, useState } from 'react'
import { CalendarCheck, Check } from 'lucide-react'
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

function JobCard({ job, canEdit, onFinish }: { job: Job; canEdit: boolean; onFinish: (id: number, s: 'done' | 'skipped') => void }) {
  return (
    <li className="flex flex-col gap-2 rounded-[var(--radius-row)] bg-sunken p-4">
      <div className="flex items-start justify-between gap-3">
        <h4 className="text-lg font-bold">{job.title}</h4>
        {job.overdue && <Badge tone="marigold">{t('Overdue')}</Badge>}
      </div>
      <p className="text-sm text-muted">{job.reason}</p>
      {job.steps.length > 0 && (
        <details className="group">
          <summary className="min-h-11 cursor-pointer py-2 text-sm font-semibold text-leaf">{t('How to do it')}</summary>
          <ol className="list-decimal space-y-1 pl-5 text-sm">
            {job.steps.map((step) => (
              <li key={step}>{step}</li>
            ))}
          </ol>
          {job.watch.length > 0 && (
            <ul className="mt-2 space-y-2 text-sm">
              {job.watch.map((w) => (
                <li key={w.slug}>
                  <span className="font-semibold">{w.name}</span>
                  {w.verdict && <span className="text-leaf"> · {t(w.verdict)}</span>}
                  <p className="text-muted">{w.identify}</p>
                  <p>{w.action}</p>
                </li>
              ))}
            </ul>
          )}
        </details>
      )}
      {canEdit && (
        <div className="flex flex-wrap gap-2">
          <Button onClick={() => onFinish(job.id, 'done')}>
            <Check className="size-4" aria-hidden /> {t(DONE[job.kind])}
          </Button>
          <Button variant="ghost" onClick={() => onFinish(job.id, 'skipped')}>
            {t('Skip')}
          </Button>
        </div>
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
      <Section title={title}>
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
                  <JobCard key={job.id} job={job} canEdit={canEdit} onFinish={finish} />
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
              <li key={job.id} className="flex items-baseline justify-between gap-3 py-2 first:pt-0 last:pb-0">
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
