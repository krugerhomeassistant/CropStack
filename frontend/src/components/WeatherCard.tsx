import { useEffect, useState } from 'react'
import {
  Cloud,
  CloudDrizzle,
  CloudFog,
  CloudLightning,
  CloudRain,
  CloudSnow,
  CloudSun,
  Droplets,
  Sun,
  Wind,
  type LucideIcon,
} from 'lucide-react'
import { api, ApiError, type DayWeather, type Weather } from '../api'
import { N_, t } from '../i18n'
import { rain, speed, tempUnit, tempValue, type Units } from '../units'

/** WMO weather interpretation codes (Open-Meteo `weather_code`) → icon and label. Display only. */
function look(code: number | null): { icon: LucideIcon; label: string } {
  if (code === null) return { icon: Cloud, label: N_('No data') }
  if (code === 0) return { icon: Sun, label: N_('Clear') }
  if (code <= 2) return { icon: CloudSun, label: N_('Partly cloudy') }
  if (code === 3) return { icon: Cloud, label: N_('Overcast') }
  if (code <= 48) return { icon: CloudFog, label: N_('Fog') }
  if (code <= 57) return { icon: CloudDrizzle, label: N_('Drizzle') }
  if (code <= 67 || (code >= 80 && code <= 82)) return { icon: CloudRain, label: N_('Rain') }
  if (code <= 77 || code === 85 || code === 86) return { icon: CloudSnow, label: N_('Snow') }
  return { icon: CloudLightning, label: N_('Thunderstorm') }
}

const weekday = (iso: string) => new Date(`${iso}T12:00:00`).toLocaleDateString(undefined, { weekday: 'short' })
const deg = (c: number | null, units: Units) => (c === null ? '–' : `${Math.round(tempValue(c, units))}°`)

function recentLine(recent: NonNullable<Weather['recent']>, units: Units): string {
  const diff = units === 'imperial' ? (recent.temp_diff_c * 9) / 5 : recent.temp_diff_c
  const warmth =
    Math.abs(diff) < 0.5
      ? t('about as warm as normal')
      : diff > 0
        ? t('{d} warmer than normal', { d: `${diff.toFixed(1)} ${tempUnit(units)}` })
        : t('{d} cooler than normal', { d: `${Math.abs(diff).toFixed(1)} ${tempUnit(units)}` })
  const p = recent.rain_percentile
  const wetness =
    p >= 95
      ? t('wetter than almost every year on record')
      : p <= 5
        ? t('drier than almost every year on record')
        : p >= 70
          ? t('wetter than {n} in 10 years', { n: Math.round(p / 10) })
          : p <= 30
            ? t('drier than {n} in 10 years', { n: Math.round((100 - p) / 10) })
            : t('rain close to normal')
  return t('Last {n} days: {warmth}; {rain} ({wetness}).', {
    n: recent.days,
    warmth,
    rain: rain(recent.rain_mm, units),
    wetness,
  })
}

export default function WeatherCard({ units }: { units: Units }) {
  const [weather, setWeather] = useState<Weather | null>(null)
  const [state, setState] = useState<'loading' | 'off' | 'error' | 'ready'>('loading')

  useEffect(() => {
    api.weather().then(
      (w) => {
        setWeather(w)
        setState('ready')
      },
      (e) => setState(e instanceof ApiError && e.status === 409 ? 'off' : 'error'),
    )
  }, [])

  if (state === 'off') return null // the household turned the forecast off; Today simply has no weather
  if (state === 'loading')
    return <section className="card h-40 animate-pulse" aria-busy="true" aria-label={t('Loading the weather')} />
  if (state === 'error' || !weather?.today)
    return <section className="card text-sm text-muted">{t('The weather forecast is not available right now.')}</section>

  const today: DayWeather = weather.today
  const now = look(today.code)
  const Icon = now.icon
  const week = weather.days.slice(1, 8)

  return (
    <section className="card flex flex-col gap-4" aria-label={t('Weather')}>
      <div className="flex items-center gap-4">
        <Icon className="size-12 shrink-0 text-leaf" aria-hidden />
        <div className="flex-1">
          <p className="text-2xl font-extrabold">
            {deg(today.tmax, units)} <span className="text-lg font-semibold text-muted">/ {deg(today.tmin, units)}</span>
          </p>
          <p className="text-sm text-muted">{t(now.label)}</p>
        </div>
        <dl className="grid grid-cols-[auto_auto] gap-x-2 gap-y-1 text-sm">
          <dt>
            <Droplets className="size-4 text-muted" aria-hidden />
            <span className="sr-only">{t('Rain')}</span>
          </dt>
          <dd>
            {today.precip_prob === null ? '–' : `${today.precip_prob}%`}
            {today.precip ? ` · ${rain(today.precip, units)}` : ''}
          </dd>
          <dt>
            <Wind className="size-4 text-muted" aria-hidden />
            <span className="sr-only">{t('Wind')}</span>
          </dt>
          <dd>{today.wind === null ? '–' : speed(today.wind, units)}</dd>
        </dl>
      </div>

      <ol className="grid grid-cols-7 gap-1 text-center text-xs" aria-label={t('Next 7 days')}>
        {week.map((d) => {
          const DayIcon = look(d.code).icon
          return (
            <li key={d.date} className="flex flex-col items-center gap-1">
              <span className="text-muted">{weekday(d.date)}</span>
              <DayIcon className="size-5 text-ink/70" aria-label={t(look(d.code).label)} />
              <span className="font-semibold">{deg(d.tmax, units)}</span>
              <span className="text-muted">{deg(d.tmin, units)}</span>
              <span className="text-[10px] text-sky-700 dark:text-sky-400">
                {d.precip_prob ? `${d.precip_prob}%` : ' '}
              </span>
            </li>
          )
        })}
      </ol>

      {weather.recent && <p className="text-sm">{recentLine(weather.recent, units)}</p>}

      <p className="text-[11px] text-muted">
        {weather.stale ? t('Last updated {when}. ', { when: new Date(weather.fetched_at).toLocaleString() }) : ''}
        {t('Forecast: {source}', { source: weather.source })}
      </p>
    </section>
  )
}
