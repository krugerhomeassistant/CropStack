import { useEffect, useState } from 'react'
import { CloudRain, Mountain, Snowflake, Sun, Thermometer, TrendingUp } from 'lucide-react'
import { api, type Climate } from '../api'
import { t } from '../i18n'
import { Badge, ErrorState, Skeleton } from './ui'
import { length, rain, rainUnit, rainValue, temp, tempUnit, tempValue, type Units } from '../units'

const MONTHS = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12].map((m) =>
  new Date(2001, m - 1, 15).toLocaleDateString(undefined, { month: 'short' }),
)

/** "09-14" → "14 Sep" in the person's locale */
const monthDay = (md: string) => {
  const [m, d] = md.split('-').map(Number)
  return new Date(2001, m - 1, d).toLocaleDateString(undefined, { day: 'numeric', month: 'short' })
}

const fmt = (v: number | null, digits = 0) => (v === null ? '–' : v.toFixed(digits))
const signed = (v: number) => `${v > 0 ? '+' : ''}${v.toFixed(1)}`

/**
 * Describes the site's climate from its own data. Nothing here switches on a climate type or a fixed
 * threshold (SPEC P1): every line is a number from the record, and frost dates appear whenever frost occurs
 * at the person's chosen risk level.
 */
export default function ClimateCard({
  gardenKey,
  units,
  onLoaded,
}: {
  gardenKey: string
  units: Units
  /** Called with each loaded climate, so the page can show charts once the archive exists. */
  onLoaded?: (climate: Climate) => void
}) {
  const [climate, setClimate] = useState<Climate | null>(null)
  const [error, setError] = useState('')

  function load() {
    setError('')
    setClimate(null)
    api.climate().then(
      (c) => {
        setClimate(c)
        onLoaded?.(c)
      },
      (err) => setError(err instanceof Error ? err.message : t('Failed to load')),
    )
  }

  // gardenKey changes when location or frost risk changes, so the card refreshes after an edit.
  useEffect(load, [gardenKey])

  if (error)
    return (
      <section className="card">
        <ErrorState message={error} onRetry={load} />
      </section>
    )

  if (!climate)
    return (
      <section className="card flex flex-col gap-4" role="status" aria-busy="true">
        <p className="text-sm text-muted">
          {t('Working out your climate from 30 years of weather records… (only slow the first time)')}
        </p>
        <Skeleton className="h-24" />
        <Skeleton className="h-40" />
      </section>
    )

  const daylight = climate.daylight_hours
  const season = climate.rain_season
  const trend = climate.trend_per_decade
  const asTemp = (c: number | null) => (c === null ? null : tempValue(c, units))
  const asRain = (mm: number | null) => (mm === null ? null : rainValue(mm, units))
  // Temperature differences convert without the 32 °F offset.
  const tempDelta = (c: number) => `${signed(units === 'imperial' ? (c * 9) / 5 : c)} ${tempUnit(units)}`

  let frostLine: string
  if (climate.frost_free) frostLine = t('No frost in {period}.', { period: climate.period })
  else if (climate.last_spring_frost)
    frostLine = t('Frost-free season about {n} days at {pct}% risk.', {
      n: climate.growing_season_days,
      pct: climate.frost_probability,
    })
  else
    frostLine = t('Frost in {pct}% of years; rarer than your {risk}% risk level, so no frost dates.', {
      pct: climate.frost_years_pct,
      risk: climate.frost_probability,
    })

  return (
    <section className="card flex flex-col gap-4" aria-label={t('Your climate')}>
      <div className="flex items-baseline justify-between">
        <h2 className="text-xl font-bold">{t('Your climate')}</h2>
        <Badge>{t('Zone {zone}', { zone: climate.zone })}</Badge>
      </div>

      <dl className="grid grid-cols-2 gap-3">
        <div>
          <dt className="flex items-center gap-1 text-xs text-muted">
            <CloudRain className="size-3.5" aria-hidden /> {t('Rain per year')}
          </dt>
          <dd className="text-xl font-bold">{rain(climate.annual_rain_mm, units)}</dd>
          {season && (
            <dd className="text-xs text-muted">
              {t('{pct}% falls {from}–{to}', {
                pct: season.share_pct,
                from: MONTHS[season.start_month - 1],
                to: MONTHS[season.end_month - 1],
              })}
            </dd>
          )}
        </div>
        <div>
          <dt className="flex items-center gap-1 text-xs text-muted">
            <Thermometer className="size-3.5" aria-hidden /> {t('Hottest day, typical year')}
          </dt>
          <dd className="text-xl font-bold">
            {climate.hottest_day_c === null ? '–' : temp(climate.hottest_day_c, units)}
          </dd>
          <dd className="text-xs text-muted">{t('coldest night {t}', { t: temp(climate.extreme_min_c, units, 1) })}</dd>
        </div>
        {climate.last_spring_frost && (
          <>
            <div>
              <dt className="text-xs text-muted">{t('Last spring frost')}</dt>
              <dd className="text-xl font-bold">{monthDay(climate.last_spring_frost)}</dd>
            </div>
            <div>
              <dt className="text-xs text-muted">{t('First autumn frost')}</dt>
              <dd className="text-xl font-bold">
                {climate.first_fall_frost ? monthDay(climate.first_fall_frost) : t('Rare')}
              </dd>
            </div>
          </>
        )}
      </dl>

      <ul className="flex flex-col gap-1 text-sm">
        <li className="flex items-center gap-2">
          <Snowflake className="size-4 shrink-0 text-muted" aria-hidden /> {frostLine}
        </li>
        {(trend.tmin !== undefined || trend.tmax !== undefined) && (
          <li className="flex items-center gap-2">
            <TrendingUp className="size-4 shrink-0 text-muted" aria-hidden />
            {[
              trend.tmax !== undefined && t('Days {d} per decade', { d: tempDelta(trend.tmax) }),
              trend.tmin !== undefined && t('nights {d} per decade', { d: tempDelta(trend.tmin) }),
            ]
              .filter(Boolean)
              .join(', ')}
          </li>
        )}
        <li className="flex items-center gap-2">
          <Sun className="size-4 shrink-0 text-muted" aria-hidden />{' '}
          {t('Daylight {min}–{max} hours', { min: Math.min(...daylight), max: Math.max(...daylight) })}
        </li>
        {climate.elevation_m !== null && (
          <li className="flex items-center gap-2">
            <Mountain className="size-4 shrink-0 text-muted" aria-hidden />{' '}
            {t('Elevation {h}', { h: length(climate.elevation_m, units) })}
          </li>
        )}
      </ul>

      <table className="w-full text-center text-xs tabular-nums">
        <caption className="sr-only">{t('Monthly averages')}</caption>
        <thead>
          <tr className="text-muted">
            <th />
            {MONTHS.map((m) => (
              <th key={m} scope="col" className="font-normal">
                <abbr title={m} className="no-underline">
                  {m[0]}
                </abbr>
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {(
            [
              ['high', t('High {u}', { u: tempUnit(units) }), climate.monthly.tmax.map(asTemp), 0],
              ['low', t('Low {u}', { u: tempUnit(units) }), climate.monthly.tmin.map(asTemp), 0],
              ['soil', t('Soil {u}', { u: tempUnit(units) }), climate.monthly.soil.map(asTemp), 0],
              ['rain', t('Rain {u}', { u: rainUnit(units) }), climate.monthly.rain.map(asRain), units === 'imperial' ? 1 : 0],
              ['frost', t('Frost nights'), climate.monthly.frost_nights, 0],
            ] as const
          ).map(([key, label, row, digits]) => (
            <tr key={key}>
              <th scope="row" className="pr-1 text-left font-semibold whitespace-nowrap">
                {label}
              </th>
              {row.map((v, i) => (
                <td key={i} className={key === 'frost' && v ? 'text-water' : undefined}>
                  {fmt(v, digits)}
                </td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>

      <p className="text-xs text-muted">
        {t(
          'Estimated from {period} records ({source}); recent years count more. Local hollows, slopes and the coast can differ from the 10–25 km grid.',
          { period: climate.period, source: climate.source },
        )}
      </p>
    </section>
  )
}
