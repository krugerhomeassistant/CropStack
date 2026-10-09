import { useEffect, useState } from 'react'
import { CloudRain, Flame, Mountain, Snowflake, Sun } from 'lucide-react'
import { api, type Climate } from '../api'

const MONTHS = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']

const REGIME: Record<Climate['rainfall_regime'], { label: string; hint: string }> = {
  winter: {
    label: 'Winter rainfall',
    hint: 'Mild, wet winters and dry summers: cool-season crops grow on the winter rain, summer crops need irrigation.',
  },
  summer: {
    label: 'Summer rainfall',
    hint: 'Rain comes with the warm season: summer crops get the water, winters are drier.',
  },
  'year-round': { label: 'Rain all year', hint: 'Rain is spread through the year.' },
  dry: { label: 'Dry', hint: 'Very little rain: everything needs irrigation.' },
}

/** "09-14" → "14 Sep" */
function monthDay(md: string): string {
  const [m, d] = md.split('-').map(Number)
  return `${d} ${MONTHS[m - 1]}`
}

const fmt = (v: number | null) => (v === null ? '–' : Math.round(v))

export default function ClimateCard({ gardenKey }: { gardenKey: string }) {
  const [climate, setClimate] = useState<Climate | null>(null)
  const [error, setError] = useState('')

  function load() {
    setError('')
    setClimate(null)
    api.climate().then(setClimate, (err) => setError(err instanceof Error ? err.message : 'Failed'))
  }

  // gardenKey changes when location or frost risk changes, so the card refreshes after an edit.
  useEffect(load, [gardenKey])

  if (error)
    return (
      <section className="card flex flex-col gap-3 text-sm">
        <p role="alert">{error}</p>
        <button className="btn-secondary" onClick={load}>
          Try again
        </button>
      </section>
    )

  if (!climate)
    return (
      <section className="card text-sm text-muted" role="status">
        Working out your climate from 30 years of weather records… (only slow the first time)
      </section>
    )

  const regime = REGIME[climate.rainfall_regime]
  const daylight = climate.daylight_hours
  // Frost dates only earn the headline where frost is a regular event.
  const frostMatters = climate.frost_years_pct >= 50 && climate.last_spring_frost !== null

  return (
    <section className="card flex flex-col gap-4" aria-label="Your climate">
      <div className="flex items-baseline justify-between">
        <h2 className="text-lg font-extrabold">Your climate</h2>
        <span className="rounded-full bg-sprout/40 px-3 py-1 text-sm font-bold">Zone {climate.zone}</span>
      </div>

      <dl className="grid grid-cols-2 gap-3">
        <div>
          <dt className="flex items-center gap-1 text-xs text-muted">
            <CloudRain className="size-3.5" aria-hidden /> {regime.label}
          </dt>
          <dd className="text-xl font-bold">{climate.annual_rain_mm} mm/yr</dd>
        </div>
        <div>
          <dt className="flex items-center gap-1 text-xs text-muted">
            <Flame className="size-3.5" aria-hidden /> Hot days (≥ 30 °C)
          </dt>
          <dd className="text-xl font-bold">{climate.hot_days_per_year} a year</dd>
        </div>
        {frostMatters && (
          <>
            <div>
              <dt className="text-xs text-muted">Last spring frost</dt>
              <dd className="text-xl font-bold">{monthDay(climate.last_spring_frost!)}</dd>
            </div>
            <div>
              <dt className="text-xs text-muted">First autumn frost</dt>
              <dd className="text-xl font-bold">
                {climate.first_fall_frost ? monthDay(climate.first_fall_frost) : 'Rare'}
              </dd>
            </div>
          </>
        )}
      </dl>

      <p className="text-sm">{regime.hint}</p>

      <ul className="flex flex-col gap-1 text-sm">
        <li className="flex items-center gap-2">
          <Snowflake className="size-4 shrink-0 text-muted" aria-hidden />
          {climate.frost_free
            ? `No frost in ${climate.period}; coldest night of a typical year ${climate.extreme_min_c} °C.`
            : frostMatters
              ? `Frost-free season ${climate.growing_season_days} days; coldest night ${climate.extreme_min_c} °C.`
              : `Frost is rare (${climate.frost_years_pct}% of years); coldest night ${climate.extreme_min_c} °C.`}
        </li>
        <li className="flex items-center gap-2">
          <Sun className="size-4 shrink-0 text-muted" aria-hidden /> Daylight {Math.min(...daylight)}–
          {Math.max(...daylight)} hours
        </li>
        {climate.elevation_m !== null && (
          <li className="flex items-center gap-2">
            <Mountain className="size-4 shrink-0 text-muted" aria-hidden /> Elevation {Math.round(climate.elevation_m)} m
          </li>
        )}
      </ul>

      <table className="w-full text-center text-xs tabular-nums">
        <caption className="sr-only">Monthly averages</caption>
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
              ['High °C', climate.monthly.tmax],
              ['Low °C', climate.monthly.tmin],
              ['Soil °C', climate.monthly.soil],
              ['Rain mm', climate.monthly.rain],
              ['Hot days', climate.monthly.hot_days],
            ] as const
          ).map(([label, row]) => (
            <tr key={label}>
              <th scope="row" className="pr-1 text-left font-semibold whitespace-nowrap">
                {label}
              </th>
              {row.map((v, i) => (
                <td key={i} className={label === 'Low °C' && v !== null && v <= 0 ? 'text-sky-600' : undefined}>
                  {fmt(v)}
                </td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>

      <p className="text-xs text-muted">
        {frostMatters && `Frost dates at ${climate.frost_probability}% risk. `}Estimated from {climate.period} records (
        {climate.source}). Local hollows, slopes and the coast can differ from the 10–25 km grid.
      </p>
    </section>
  )
}
