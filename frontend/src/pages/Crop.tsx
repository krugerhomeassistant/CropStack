import { useEffect, useState, type ReactNode } from 'react'
import { useParams } from 'react-router'
import { BookOpen } from 'lucide-react'
import {
  api,
  ApiError,
  type CatalogItem,
  type CatalogSource,
  type CropData,
  type Evidence,
  type Fact,
  type FactOrList,
  type Range,
} from '../api'
import { Badge, EmptyState, ErrorState, PageHeader, Section, Skeleton } from '../components/ui'
import SowingWindows from '../components/SowingWindows'
import { N_, t } from '../i18n'
import { useApp } from '../state'
import { cm, metres, rain, temp, type Units } from '../units'

const EVIDENCE: Record<Evidence, string> = {
  'peer-reviewed': N_('Peer-reviewed study'),
  government: N_('Official guideline'),
  'extension-service': N_('Extension service'),
  model: N_('Crop-model calibration'),
  'grower-reported': N_('Reported by growers'),
  traditional: N_('Traditional knowledge'),
}

const LIFE_CYCLE = { annual: N_('Annual'), biennial: N_('Biennial'), perennial: N_('Perennial') }
const SUN: Record<string, string> = {
  full_sun: N_('Full sun'),
  partial_sun: N_('Partial sun'),
  partial_shade: N_('Partial shade'),
  shade: N_('Shade'),
}

const list = (f: FactOrList | undefined): Fact[] => (f === undefined ? [] : Array.isArray(f) ? f : [f])
const first = (f: FactOrList | undefined): Fact | undefined => list(f)[0]
const num = (f: FactOrList | undefined) => first(f)?.value as number | undefined
const range = (f: FactOrList | undefined) => first(f)?.value as Range | undefined

/**
 * Numbered citations, collected in the order values are rendered (JSX children evaluate left to right), and listed
 * under Sources at the end of the page. One number per source and locator.
 */
class Notes {
  keys: string[] = []
  entries: { ref: string; locator?: string | null; retrieved?: string | null; evidence: Evidence }[] = []

  cite(...facts: (FactOrList | undefined)[]): ReactNode {
    const numbers = new Set<number>()
    for (const fact of facts.flatMap(list))
      for (const s of fact.sources) {
        const key = `${s.ref}|${s.locator ?? ''}`
        if (!this.keys.includes(key)) {
          this.keys.push(key)
          this.entries.push({ ref: s.ref, locator: s.locator, retrieved: s.retrieved, evidence: fact.evidence })
        }
        numbers.add(this.keys.indexOf(key) + 1)
      }
    if (!numbers.size) return null
    return (
      <sup className="ml-0.5 text-xs font-semibold">
        {[...numbers].map((n, i) => (
          <span key={n}>
            {i > 0 && ','}
            <a href={`#source-${n}`} className="text-leaf hover:underline" aria-label={t('Source {n}', { n })}>
              {n}
            </a>
          </span>
        ))}
      </sup>
    )
  }
}

/** A row in a ruled definition list: label, the value in plain words, and its citation numbers. */
function Row({ label, children, low }: { label: string; children: ReactNode; low?: boolean }) {
  return (
    <div className="grid gap-1 py-3 sm:grid-cols-[12rem_1fr] sm:gap-4">
      <dt className="text-sm font-semibold text-muted">{label}</dt>
      <dd>
        {children}
        {low && <span className="block text-sm text-muted">{t('Reported by growers; treat as a rough guide.')}</span>}
      </dd>
    </div>
  )
}

function Germination({ data, units, notes }: { data: CropData; units: Units; notes: Notes }) {
  const germ = data.requirements?.soil_temperature?.germination
  const emergence = list(data.params?.days_to_emergence)
  const g = range(germ)
  if (!g && !emergence.length) return null
  return (
    <Section title={t('Sowing')}>
      <dl className="-my-3 divide-y divide-line">
        {g && (
          <Row label={t('Soil temperature to germinate')}>
            {t('Germinates between {min} and {max}, best at {opt}.', {
              min: g.min == null ? '–' : temp(g.min, units),
              max: g.max == null ? '–' : temp(g.max, units),
              opt: g.opt == null ? '–' : temp(g.opt, units),
            })}
            {notes.cite(germ)}
          </Row>
        )}
        {emergence.length > 0 && (
          <Row label={t('Days until seedlings appear')}>
            <ol className="flex flex-wrap gap-2" aria-label={t('Days to emergence by soil temperature')}>
              {emergence.map((f) => (
                <li
                  key={String(f.qualifiers?.soil_temp_c)}
                  className="rounded-[var(--radius-row)] bg-sunken px-3 py-1.5 text-center"
                >
                  <span className="block text-xs text-muted">{temp(Number(f.qualifiers?.soil_temp_c), units)}</span>
                  <span className="font-display text-lg font-bold">{t('{n} d', { n: f.value as number })}</span>
                </li>
              ))}
            </ol>
            <span className="mt-1 block text-sm text-muted">
              {t('Soil temperature at sowing depth.')}
              {notes.cite(emergence)}
            </span>
          </Row>
        )}
      </dl>
    </Section>
  )
}

function Conditions({ data, units, notes }: { data: CropData; units: Units; notes: Notes }) {
  const air = data.requirements?.temperature ?? {}
  const low = num(air.stress_min)
  const high = num(air.stress_max)
  const best = range(air.optimal)
  const ph = data.requirements?.soil?.ph
  const acidity = range(ph)
  const cycle = range(data.params?.cycle_days)
  const rainfall = data.params?.annual_rainfall
  const yearly = range(rainfall)
  if (low == null && !acidity && !cycle && !yearly) return null
  const fixed = (n?: number | null) => (n == null ? '–' : n.toFixed(1))
  return (
    <Section title={t('Growing conditions')} description={t('The conditions this crop is usually grown in, from FAO.')}>
      <dl className="-my-3 divide-y divide-line">
        {low != null && high != null && best && (
          <Row label={t('Air temperature')}>
            {t('Grows between {min} and {max}, best between {from} and {to}.', {
              min: temp(low, units),
              max: temp(high, units),
              from: temp(best.min ?? low, units),
              to: temp(best.max ?? high, units),
            })}
            {notes.cite(air.stress_min, air.optimal, air.stress_max)}
          </Row>
        )}
        {acidity && (
          <Row label={t('Soil acidity (pH)')}>
            {t('Copes with pH {min} to {max}, best between {from} and {to}.', {
              min: fixed(acidity.min),
              max: fixed(acidity.max),
              from: fixed(acidity.opt_min),
              to: fixed(acidity.opt_max),
            })}
            {notes.cite(ph)}
          </Row>
        )}
        {cycle && (
          <Row label={t('Growing cycle')}>
            {t('{min} to {max} days from sowing to the end of the harvest.', { min: cycle.min ?? '–', max: cycle.max ?? '–' })}
            {notes.cite(data.params?.cycle_days)}
          </Row>
        )}
        {yearly && (
          <Row label={t('Rain it is grown in')}>
            {t('Usually grown where a year brings {from} to {to} of rain; it copes with {min} to {max}.', {
              from: rain(yearly.opt_min ?? 0, units),
              to: rain(yearly.opt_max ?? 0, units),
              min: rain(yearly.min ?? 0, units),
              max: rain(yearly.max ?? 0, units),
            })}
            {notes.cite(rainfall)}
          </Row>
        )}
      </dl>
    </Section>
  )
}

function Water({ data, units, notes }: { data: CropData; units: Units; notes: Notes }) {
  const w = data.requirements?.water ?? {}
  const roots = range(w.root_depth)
  const p = num(w.depletion_fraction)
  const [ini, mid, late] = [num(w.kc_initial), num(w.kc_mid), num(w.kc_late)]
  if (!roots && p === undefined && mid === undefined) return null
  return (
    <Section title={t('Water')}>
      <dl className="-my-3 divide-y divide-line">
        {mid !== undefined && (
          <Row label={t('Water use')}>
            {t('{ini} of a lawn’s water use when young, {mid} at full size, {late} near the end.', {
              ini: ini === undefined ? '–' : `${Math.round(ini * 100)}%`,
              mid: `${Math.round(mid * 100)}%`,
              late: late === undefined ? '–' : `${Math.round(late * 100)}%`,
            })}
            {notes.cite(w.kc_initial, w.kc_mid, w.kc_late)}
          </Row>
        )}
        {roots?.min != null && roots.max != null && (
          <Row label={t('Root depth')}>
            {t('Roots reach {min} to {max} deep in open soil.', {
              min: metres(roots.min, units),
              max: metres(roots.max, units),
            })}
            {notes.cite(w.root_depth)}
          </Row>
        )}
        {p !== undefined && (
          <Row label={t('When to water')}>
            {t('Before about {pct}% of the water the roots can reach is used up.', { pct: Math.round(p * 100) })}
            {notes.cite(w.depletion_fraction)}
          </Row>
        )}
      </dl>
    </Section>
  )
}

function Size({ data, units, notes }: { data: CropData; units: Units; notes: Notes }) {
  const params = data.params ?? {}
  const rows: ReactNode[] = []
  const grower = (f: FactOrList | undefined) => first(f)?.evidence === 'grower-reported'
  if (num(params.row_spacing) !== undefined)
    rows.push(
      <Row key="row" label={t('Row spacing')} low={grower(params.row_spacing)}>
        {cm(num(params.row_spacing)!, units)}
        {notes.cite(params.row_spacing)}
      </Row>,
    )
  if (num(params.plant_spread) !== undefined)
    rows.push(
      <Row key="spread" label={t('Plant width')} low={grower(params.plant_spread)}>
        {cm(num(params.plant_spread)!, units)}
        {notes.cite(params.plant_spread)}
      </Row>,
    )
  const height = num(params.height_max) ?? undefined
  if (height !== undefined)
    rows.push(
      <Row key="height" label={t('Height')}>
        {t('Up to {h}', { h: metres(height, units) })}
        {notes.cite(params.height_max)}
      </Row>,
    )
  else if (num(params.height) !== undefined)
    rows.push(
      <Row key="height" label={t('Height')} low={grower(params.height)}>
        {cm(num(params.height)!, units)}
        {notes.cite(params.height)}
      </Row>,
    )
  const sun = first(params.sun)?.value as string | undefined
  if (sun && SUN[sun])
    rows.push(
      <Row key="sun" label={t('Light')} low={grower(params.sun)}>
        {t(SUN[sun])}
        {notes.cite(params.sun)}
      </Row>,
    )
  if (!rows.length) return null
  return (
    <Section title={t('Size and spacing')}>
      <dl className="-my-3 divide-y divide-line">{rows}</dl>
    </Section>
  )
}

const STAGES = ['initial', 'development', 'mid', 'late'] as const

/** FAO-56 labels are lower case ("california desert usa", "apr may"): sentence case them for display. */
const label = (v: string | number | null | undefined) =>
  v == null ? '–' : String(v).replace(/\busa\b/, 'USA').replace(/^./, (c) => c.toUpperCase())
const months = (v: string | number | null | undefined) =>
  v == null ? '–' : String(v).replace(/\b[a-z]/g, (c) => c.toUpperCase())

function Stages({ data, notes }: { data: CropData; notes: Notes }) {
  const params = data.params ?? {}
  const byStage = STAGES.map((s) => list(params[`stage_days_${s}`]))
  if (!byStage[0].length) return null
  return (
    <Section
      title={t('Growth stages')}
      description={t('Days in each stage in field trials. Your garden’s own timing will come from its weather.')}
    >
      <div className="-mx-5 overflow-x-auto px-5">
        <table className="w-full min-w-[32rem] text-sm">
          <thead className="text-left text-muted">
            <tr>
              <th className="py-2 pr-3 font-semibold">{t('Trial region')}</th>
              <th className="py-2 pr-3 font-semibold">{t('Sown')}</th>
              <th className="py-2 pr-3 text-right font-semibold">{t('Establishing')}</th>
              <th className="py-2 pr-3 text-right font-semibold">{t('Growing')}</th>
              <th className="py-2 pr-3 text-right font-semibold">{t('Full size')}</th>
              <th className="py-2 text-right font-semibold">{t('Ripening')}</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-line">
            {byStage[0].map((row, i) => (
              <tr key={i}>
                <td className="py-2 pr-3">{label(row.qualifiers?.region)}</td>
                <td className="py-2 pr-3">{months(row.qualifiers?.planting)}</td>
                {byStage.map((stage, s) => (
                  <td key={STAGES[s]} className="py-2 pr-3 text-right tabular-nums last:pr-0">
                    {stage[i]?.value as number}
                  </td>
                ))}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      <p className="text-sm text-muted">
        {t('Days per stage.')}
        {notes.cite(...byStage)}
      </p>
    </Section>
  )
}

function Sources({ notes, sources }: { notes: Notes; sources: Record<string, CatalogSource> }) {
  if (!notes.entries.length) return null
  return (
    <Section title={t('Sources')}>
      <ol className="flex flex-col gap-3 text-sm">
        {notes.entries.map((e, i) => {
          const s = sources[e.ref]
          return (
            <li key={i} id={`source-${i + 1}`} className="grid grid-cols-[1.5rem_1fr] gap-1 scroll-mt-6">
              <span className="font-semibold text-muted">{i + 1}.</span>
              <span>
                {s ? (
                  <a href={s.url} target="_blank" rel="noreferrer" className="font-semibold hover:underline">
                    {s.title}
                  </a>
                ) : (
                  <span className="font-semibold">{e.ref}</span>
                )}
                {s?.author && <span className="text-muted">, {s.author}</span>}
                {e.locator && (
                  <span className="block text-muted">
                    {e.locator.startsWith('http') ? (
                      <a href={e.locator} target="_blank" rel="noreferrer" className="break-all hover:underline">
                        {t('Archived page')}
                      </a>
                    ) : (
                      e.locator
                    )}
                  </span>
                )}
                <span className="block text-muted">
                  {t(EVIDENCE[e.evidence])}
                  {s && `, ${s.license}`}
                  {e.retrieved &&
                    `, ${t('retrieved {date}', { date: new Date(`${e.retrieved}T12:00:00`).toLocaleDateString() })}`}
                </span>
              </span>
            </li>
          )
        })}
      </ol>
    </Section>
  )
}

export default function Crop() {
  const { slug = '' } = useParams()
  const { user } = useApp()
  const [item, setItem] = useState<CatalogItem<CropData> | null>(null)
  const [error, setError] = useState<{ message: string; missing: boolean } | null>(null)

  function load() {
    setError(null)
    setItem(null)
    api
      .crop(slug)
      .then(setItem, (e) =>
        setError({
          message: e instanceof Error ? e.message : t('Failed to load'),
          missing: e instanceof ApiError && e.status === 404,
        }),
      )
  }
  useEffect(load, [slug])

  if (error)
    return (
      <>
        <PageHeader back title={t('Crops')} />
        <section className="card">
          {error.missing ? (
            <EmptyState icon={BookOpen} title={t('This crop is not in the catalog')}>
              {t('It may have been renamed. Go back to the list to find it.')}
            </EmptyState>
          ) : (
            <ErrorState message={error.message} onRetry={load} />
          )}
        </section>
      </>
    )

  if (!item)
    return (
      <div className="flex flex-col gap-6" aria-busy="true" aria-label={t('Loading crop')}>
        <Skeleton className="h-16" />
        <Skeleton className="h-40" />
        <Skeleton className="h-40" />
      </div>
    )

  const data = item.data
  const units = user.prefs.units
  const notes = new Notes()
  const others = Object.entries(data.names).filter(([lang]) => lang !== 'en')

  return (
    <>
      <PageHeader
        back
        title={data.names.en?.[0] ?? data.slug}
        subtitle={
          <>
            <i>{data.scientific_name}</i>, {data.family}
          </>
        }
      />

      <div className="flex flex-wrap gap-2">
        <Badge tone="muted">{t(LIFE_CYCLE[data.life_cycle])}</Badge>
        {data.rotation_group && <Badge tone="muted">{t('Rotation: {group}', { group: data.rotation_group })}</Badge>}
        {others.map(([lang, names]) => (
          <Badge key={lang} tone="muted">
            {lang === 'af' ? t('Afrikaans: {name}', { name: names[0] }) : `${lang}: ${names[0]}`}
          </Badge>
        ))}
      </div>

      {data.description && <p className="max-w-prose text-lg">{data.description}</p>}

      <SowingWindows slug={slug} />

      <div className="flex flex-col gap-6 lg:grid lg:grid-cols-2 lg:items-start">
        <Germination data={data} units={units} notes={notes} />
        <Conditions data={data} units={units} notes={notes} />
        <Water data={data} units={units} notes={notes} />
        <Size data={data} units={units} notes={notes} />
      </div>
      <Stages data={data} notes={notes} />
      <Sources notes={notes} sources={item.sources} />
    </>
  )
}
