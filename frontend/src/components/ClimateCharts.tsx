import { useEffect, useState } from 'react'
import { api, type Bands, type Climate, type Probability } from '../api'
import { t } from '../i18n'
import { rainUnit, rainValue, tempUnit, tempValue, type Units } from '../units'
import { dayOfYear, MonthBars, YearChart, type Series } from './charts'
import { ErrorState, Section, Skeleton } from './ui'

type Data = { tmax: Bands; tmin: Bands; soil: Bands; frost: Probability }

const warm = 'var(--color-chart-warm)'
const cool = 'var(--color-chart-cool)'

/** Day length for each day of the year, from the twelve mid-month values (linear, wrapping over the year end). */
function dailyDaylight(monthly: number[]): number[] {
  const mid = [14, 45, 73, 104, 134, 165, 195, 226, 257, 287, 318, 348] // 15th of each month, day of a 365-day year
  const xs = [mid[11] - 365, ...mid, mid[0] + 365] // one point each side so December and January join up
  const ys = [monthly[11], ...monthly, monthly[0]]
  return Array.from({ length: 365 }, (_, d) => {
    const k = xs.findIndex((x, i) => x <= d && d < xs[i + 1])
    return ys[k] + ((ys[k + 1] - ys[k]) * (d - xs[k])) / (xs[k + 1] - xs[k])
  })
}

/**
 * The shape of the year at the garden: typical temperatures with their range, soil, rain, day length, and the
 * chance of a freezing night only where freezing happens at all (SPEC P1: nothing is switched on by a climate type).
 */
export default function ClimateCharts({ climate, units }: { climate: Climate; units: Units }) {
  const [data, setData] = useState<Data | null>(null)
  const [error, setError] = useState('')

  function load() {
    setError('')
    setData(null)
    Promise.all([api.bands('tmax'), api.bands('tmin'), api.bands('soil_t'), api.probability('tmin', 'le', 0)]).then(
      ([tmax, tmin, soil, frost]) => setData({ tmax, tmin, soil, frost }),
      (e) => setError(e instanceof Error ? e.message : t('Failed to load')),
    )
  }
  // The garden's location or frost risk changing gives a new climate object, so the charts follow.
  useEffect(load, [climate])

  if (error)
    return (
      <Section>
        <ErrorState message={error} onRetry={load} />
      </Section>
    )
  if (!data)
    return (
      <Section aria-label={t('Loading the charts')}>
        <Skeleton className="h-56" />
      </Section>
    )

  const deg = (v: number) => `${Math.round(v)}${tempUnit(units)}`
  const degShort = (v: number) => `${Math.round(v)}°`
  const conv = (a: (number | null)[]) => a.map((v) => (v === null ? null : tempValue(v, units)))
  const band = (name: string, color: string, b: Bands): Series => ({
    name,
    color,
    values: conv(b.p50),
    low: conv(b.p10),
    high: conv(b.p90),
  })
  const today = dayOfYear()
  const rainFormat = (v: number) => `${v.toFixed(units === 'imperial' ? 1 : 0)} ${rainUnit(units)}`
  const freezes = Math.max(...data.frost.days) > 0.01
  const daylight = dailyDaylight(climate.daylight_hours)

  return (
    <>
      <Section
        title={t('Temperature through the year')}
        description={t('The line is a typical day. The shaded band is the range in 8 years out of 10.')}
      >
        <YearChart
          title={t('Temperature through the year')}
          series={[band(t('Daily high'), warm, data.tmax), band(t('Daily low'), cool, data.tmin)]}
          format={deg}
          axisFormat={degShort}
          todayIndex={today}
        />
      </Section>

      <Section title={t('Rain per month')} description={t('Average over {years}.', { years: climate.period })}>
        <MonthBars
          title={t('Rain per month')}
          values={climate.monthly.rain.map((v) => (v === null ? null : rainValue(v, units)))}
          color={cool}
          format={rainFormat}
          axisFormat={(v) => String(v)}
          highlight={new Date().getMonth()}
        />
      </Section>

      <Section
        title={t('Soil temperature')}
        description={t('Top 7 cm of soil. Seeds germinate and roots grow at the temperatures shown on each crop page.')}
      >
        <YearChart
          title={t('Soil temperature')}
          series={[band(t('Soil temperature'), 'var(--color-feed)', data.soil)]}
          format={deg}
          axisFormat={degShort}
          todayIndex={today}
        />
      </Section>

      {freezes && (
        <Section
          title={t('Chance of a freezing night')}
          description={t('How often the night low reaches 0 °C (32 °F) or below, on each day of the year.')}
        >
          <YearChart
            title={t('Chance of a freezing night')}
            series={[{ name: t('Chance of a freezing night'), color: cool, values: data.frost.days.map((p) => p * 100) }]}
            format={(v) => `${Math.round(v)}%`}
            yMin={0}
            yMax={100}
            todayIndex={today}
          />
        </Section>
      )}

      <Section title={t('Day length')} description={t('Hours between sunrise and sunset.')}>
        <YearChart
          title={t('Day length')}
          series={[{ name: t('Day length'), color: 'var(--color-leaf)', values: daylight }]}
          format={(v) => t('{h} hours', { h: v.toFixed(1) })}
          axisFormat={(v) => `${v}h`}
          todayIndex={today}
        />
      </Section>
    </>
  )
}
