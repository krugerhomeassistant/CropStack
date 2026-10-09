import { useEffect, useState } from 'react'
import { api, ApiError, type CropWindows } from '../api'
import { t } from '../i18n'
import { YearChart } from './charts'
import { ErrorState, Section, Skeleton } from './ui'

const FACTOR: Record<string, string> = {
  matures: 'Not enough warm days to ripen before the weather turns',
  germination: 'Soil too cold for the seed to come up',
  frost: 'Frost kills it before harvest',
  heat: 'Long hot spells stop it growing',
}

/** "03-25" as a short local date. */
const day = (md: string) =>
  new Date(2001, Number(md.slice(0, 2)) - 1, Number(md.slice(3))).toLocaleDateString(undefined, {
    day: 'numeric',
    month: 'short',
  })

/** When to direct-sow this crop here, worked out from its requirements and the local climate record. */
export default function SowingWindows({ slug }: { slug: string }) {
  const [data, setData] = useState<CropWindows | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [noGarden, setNoGarden] = useState(false)

  function load() {
    setError(null)
    setData(null)
    api.cropWindows(slug).then(setData, (e) => {
      if (e instanceof ApiError && e.status === 404) setNoGarden(true)
      else setError(e instanceof Error ? e.message : t('Failed to load'))
    })
  }
  useEffect(load, [slug])

  if (noGarden) return null // no garden yet: the Garden page asks for the location
  const title = t('When to sow here')
  if (error)
    return (
      <Section title={title}>
        <ErrorState message={error} onRetry={load} />
      </Section>
    )
  if (!data) return <Skeleton className="h-56" />
  if (!data.usable)
    return (
      <Section title={title}>
        <p className="text-muted">{t('Not enough is known yet to work this out: {what}.', { what: data.missing.join(', ') })}</p>
      </Section>
    )

  const { verdict, windows } = data
  const best = windows[0]
  const headline =
    verdict.state === 'yes'
      ? windows.map((w) => (w.all_year ? t('Any time of year') : `${day(w.start)} – ${day(w.end)}`)).join(', ')
      : verdict.state === 'risky'
        ? t('Only with a real risk of losing it: the best day works in {pct}% of years.', {
            pct: Math.round(verdict.best_success * 100),
          })
        : t('Not likely to succeed here when sown directly.')

  return (
    <Section
      title={title}
      description={t('Direct sowing. Each year on record is one possible season; a day counts when the crop succeeds in at least {pct}% of them.', {
        pct: Math.round(verdict.threshold * 100),
      })}
    >
      <p className="text-lg font-semibold">{headline}</p>
      {best && !best.all_year && (
        <p className="text-muted">
          {t('Best: {from} – {to}. Ready after about {days} days (most years {low}–{high}).', {
            from: day(best.best_start),
            to: day(best.best_end),
            days: best.days_to_maturity.p50,
            low: best.days_to_maturity.p10,
            high: best.days_to_maturity.p90,
          })}
        </p>
      )}
      {verdict.state !== 'yes' && verdict.blockers.length > 0 && (
        <ul className="list-disc pl-5 text-muted">
          {verdict.blockers.map((b) => (
            <li key={b}>{t(FACTOR[b] ?? b)}</li>
          ))}
        </ul>
      )}
      <YearChart
        title={t('Chance of success by sowing day')}
        series={[{ name: t('Chance of success'), color: 'var(--color-leaf)', values: data.success_by_day.map((p) => p * 100) }]}
        format={(v) => `${Math.round(v)}%`}
        yMin={0}
        yMax={100}
      />
      {data.estimates.length > 0 && (
        <p className="text-sm text-muted">{t('Some limits used here are estimates, marked in the sources below.')}</p>
      )}
    </Section>
  )
}
