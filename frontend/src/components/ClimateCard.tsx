import { useEffect, useState } from 'react'
import { CloudRain, Flame, Mountain, Snowflake, Sun } from 'lucide-react'
import { api, type Climate } from '../api'
import { N_, t } from '../i18n'
import { length, rain, rainUnit, rainValue, temp, tempUnit, tempValue, type Units } from '../units'

const MONTHS = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12].map((m) =>
  new Date(2001, m - 1, 15).toLocaleDateString(undefined, { month: 'short' }),
)

const REGIME: Record<Climate['rainfall_regime'], { label: string; hint: string }> = {
  winter: {
    label: N_('Winter rainfall'),
    hint: N_('Mild, wet winters and dry summers: cool-season crops grow on the winter rain, summer crops need irrigation.'),
  },
  summer: {
    label: N_('Summer rainfall'),
    hint: N_('Rain comes with the warm season: summer crops get the water, winters are drier.'),
  },
  'year-round': { label: N_('Rain all year'), hint: N_('Rain is spread through the year.') },
  dry: { label: N_('Dry'), hint: N_('Very little rain: everything needs irrigation.') },
}

/** "09-14" → "14 Sep" */
function monthDay(md: string): string {
  const [m, d] = md.split('-').map(Number)
  return `${d} ${MONTHS[m - 1]}`
}

const fmt = (v: number | null, digits = 0) => (v === null ? '–' : v.toFixed(digits))
const frosty = (c: number | null) => c !== null && c <= 0  // average low at or below freezing

export default function ClimateCard({ gardenKey, units }: { gardenKey: string; units: Units }) {
  const [climate, setClimate] = useState<Climate | null>(null)
  const [error, setError] = useState('')

  function load() {
    setError('')
    setClimate(null)
    api.climate().then(setClimate, (err) => setError(err instanceof Error ? err.message : t('Failed to load')))
  }

  // gardenKey changes when location or frost risk changes, so the card refreshes after an edit.
  useEffect(load, [gardenKey])

  if (error)
    return (
      <section className="card flex flex-col gap-3 text-sm">
        <p role="alert">{error}</p>
        <button className="btn-secondary" onClick={load}>
          {t('Try again')}
        </button>
      </section>
    )

  if (!climate)
    return (
      <section className="card text-sm text-muted" role="status">
        {t('Working out your climate from 30 years of weather records… (only slow the first time)')}
      </section>
    )

  const regime = REGIME[climate.rainfall_regime]
  const daylight = climate.daylight_hours
  // Frost dates only earn the headline where frost is a regular event.
  const frostMatters = climate.frost_years_pct >= 50 && climate.last_spring_frost !== null
  const coldest = temp(climate.extreme_min_c, units, 1)
  const asTemp = (c: number | null) => (c === null ? null : tempValue(c, units))
  const asRain = (mm: number | null) => (mm === null ? null : rainValue(mm, units))

  return (
    <section className="card flex flex-col gap-4" aria-label={t('Your climate')}>
      <div className="flex items-baseline justify-between">
        <h2 className="text-lg font-extrabold">{t('Your climate')}</h2>
        <span className="rounded-full bg-sprout/40 px-3 py-1 text-sm font-bold">{t('Zone {zone}', { zone: climate.zone })}</span>
      </div>

      <dl className="grid grid-cols-2 gap-3">
        <div>
          <dt className="flex items-center gap-1 text-xs text-muted">
            <CloudRain className="size-3.5" aria-hidden /> {t(regime.label)}
          </dt>
          <dd className="text-xl font-bold">{t('{amount} a year', { amount: rain(climate.annual_rain_mm, units) })}</dd>
        </div>
        <div>
          <dt className="flex items-center gap-1 text-xs text-muted">
            <Flame className="size-3.5" aria-hidden /> {t('Hot days (≥ {t})', { t: temp(30, units) })}
          </dt>
          <dd className="text-xl font-bold">{t('{n} a year', { n: climate.hot_days_per_year })}</dd>
        </div>
        {frostMatters && (
          <>
            <div>
              <dt className="text-xs text-muted">{t('Last spring frost')}</dt>
              <dd className="text-xl font-bold">{monthDay(climate.last_spring_frost!)}</dd>
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

      <p className="text-sm">{t(regime.hint)}</p>

      <ul className="flex flex-col gap-1 text-sm">
        <li className="flex items-center gap-2">
          <Snowflake className="size-4 shrink-0 text-muted" aria-hidden />
          {climate.frost_free
            ? t('No frost in {period}; coldest night of a typical year {t}.', { period: climate.period, t: coldest })
            : frostMatters
              ? t('Frost-free season {n} days; coldest night {t}.', { n: climate.growing_season_days, t: coldest })
              : t('Frost is rare ({pct}% of years); coldest night {t}.', { pct: climate.frost_years_pct, t: coldest })}
        </li>
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
              ['high', t('High {u}', { u: tempUnit(units) }), climate.monthly.tmax.map(asTemp)],
              ['low', t('Low {u}', { u: tempUnit(units) }), climate.monthly.tmin.map(asTemp)],
              ['soil', t('Soil {u}', { u: tempUnit(units) }), climate.monthly.soil.map(asTemp)],
              ['rain', t('Rain {u}', { u: rainUnit(units) }), climate.monthly.rain.map(asRain)],
              ['hot', t('Hot days'), climate.monthly.hot_days],
            ] as const
          ).map(([key, label, row]) => (
            <tr key={key}>
              <th scope="row" className="pr-1 text-left font-semibold whitespace-nowrap">
                {label}
              </th>
              {row.map((v, i) => (
                <td key={i} className={key === 'low' && frosty(climate.monthly.tmin[i]) ? 'text-sky-600' : undefined}>
                  {fmt(v, key === 'rain' && units === 'imperial' ? 1 : 0)}
                </td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>

      <p className="text-xs text-muted">
        {frostMatters && t('Frost dates at {pct}% risk.', { pct: climate.frost_probability }) + ' '}
        {t('Estimated from {period} records ({source}). Local hollows, slopes and the coast can differ from the 10–25 km grid.', {
          period: climate.period,
          source: climate.source,
        })}
      </p>
    </section>
  )
}
