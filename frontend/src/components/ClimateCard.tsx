import { useEffect, useState } from 'react'
import { Snowflake, Sun, Thermometer } from 'lucide-react'
import { api, type Climate } from '../api'

const MONTHS = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']

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

  const daylight = climate.daylight_hours
  return (
    <section className="card flex flex-col gap-4" aria-label="Your climate">
      <div className="flex items-baseline justify-between">
        <h2 className="text-lg font-extrabold">Your climate</h2>
        <span className="rounded-full bg-sprout/40 px-3 py-1 text-sm font-bold">Zone {climate.zone}</span>
      </div>

      {climate.frost_free ? (
        <p className="flex items-center gap-2">
          <Sun className="size-5 text-leaf" aria-hidden /> No frost recorded in {climate.period}.
        </p>
      ) : (
        <dl className="grid grid-cols-2 gap-3">
          <div>
            <dt className="text-xs text-muted">Last spring frost</dt>
            <dd className="text-xl font-bold">
              {climate.last_spring_frost ? monthDay(climate.last_spring_frost) : 'Rare'}
            </dd>
          </div>
          <div>
            <dt className="text-xs text-muted">First autumn frost</dt>
            <dd className="text-xl font-bold">
              {climate.first_fall_frost ? monthDay(climate.first_fall_frost) : 'Rare'}
            </dd>
          </div>
          <div>
            <dt className="text-xs text-muted">Frost-free season</dt>
            <dd className="font-bold">{climate.growing_season_days} days</dd>
          </div>
          <div>
            <dt className="text-xs text-muted">Years with frost</dt>
            <dd className="font-bold">{climate.frost_years_pct}%</dd>
          </div>
        </dl>
      )}

      <ul className="flex flex-col gap-1 text-sm">
        <li className="flex items-center gap-2">
          <Snowflake className="size-4 text-muted" aria-hidden /> Coldest night of a typical year:{' '}
          {climate.extreme_min_c} °C
        </li>
        <li className="flex items-center gap-2">
          <Sun className="size-4 text-muted" aria-hidden /> Daylight {Math.min(...daylight)}–{Math.max(...daylight)}{' '}
          hours
        </li>
        {climate.elevation_m !== null && (
          <li className="flex items-center gap-2">
            <Thermometer className="size-4 text-muted" aria-hidden /> Elevation {Math.round(climate.elevation_m)} m
          </li>
        )}
      </ul>

      <div className="-mx-1 overflow-x-auto">
        <table className="w-full text-center text-xs tabular-nums">
          <caption className="sr-only">Monthly averages in °C</caption>
          <thead>
            <tr className="text-muted">
              <th className="text-left font-normal">°C</th>
              {MONTHS.map((m) => (
                <th key={m} scope="col" className="font-normal">
                  {m[0]}
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {(
              [
                ['High', climate.monthly.tmax],
                ['Low', climate.monthly.tmin],
                ['Soil', climate.monthly.soil],
              ] as const
            ).map(([label, row]) => (
              <tr key={label}>
                <th scope="row" className="text-left font-semibold">
                  {label}
                </th>
                {row.map((v, i) => (
                  <td key={i} className={v !== null && v <= 0 ? 'text-sky-600' : undefined}>
                    {fmt(v)}
                  </td>
                ))}
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      <p className="text-xs text-muted">
        Frost dates at {climate.frost_probability}% risk, estimated from {climate.period} records (
        {climate.source}). Local hollows and slopes can be colder than the 10–25 km grid.
      </p>
    </section>
  )
}
