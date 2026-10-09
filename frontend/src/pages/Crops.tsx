import { useEffect, useMemo, useState } from 'react'
import { Link } from 'react-router'
import { ChevronRight, Search } from 'lucide-react'
import { api, type CropSummary } from '../api'
import { EmptyState, ErrorState, PageHeader, Skeleton } from '../components/ui'
import { t } from '../i18n'

const displayName = (c: CropSummary) => c.names.en?.[0] ?? c.slug

/** Every name a person might type: English and Afrikaans names, the scientific name and the family. */
const haystack = (c: CropSummary) =>
  [...Object.values(c.names).flat(), c.scientific_name, c.family].join(' ').toLowerCase()

export default function Crops() {
  const [crops, setCrops] = useState<CropSummary[] | null>(null)
  const [error, setError] = useState('')
  const [query, setQuery] = useState('')

  function load() {
    setError('')
    api.crops().then(
      (list) => setCrops(list.sort((a, b) => displayName(a).localeCompare(displayName(b)))),
      (e) => setError(e instanceof Error ? e.message : t('Failed to load')),
    )
  }
  useEffect(load, [])

  const shown = useMemo(() => {
    const q = query.trim().toLowerCase()
    return crops?.filter((c) => !q || haystack(c).includes(q)) ?? []
  }, [crops, query])

  return (
    <>
      <PageHeader
        title={t('Crops')}
        subtitle={t('What CropStack knows about each crop, and where every number comes from.')}
      />

      <div className="relative">
        <Search className="pointer-events-none absolute top-3 left-3 size-5 text-muted" aria-hidden />
        <input
          type="search"
          className="input pl-10"
          placeholder={t('Name, Afrikaans name or family')}
          aria-label={t('Search crops')}
          value={query}
          onChange={(e) => setQuery(e.target.value)}
        />
      </div>

      {error ? (
        <section className="card">
          <ErrorState message={error} onRetry={load} />
        </section>
      ) : !crops ? (
        <section className="card flex flex-col gap-3" aria-busy="true" aria-label={t('Loading crops')}>
          {[0, 1, 2, 3].map((i) => (
            <Skeleton key={i} className="h-12" />
          ))}
        </section>
      ) : shown.length === 0 ? (
        <section className="card">
          <EmptyState icon={Search} title={t('No crops match "{q}"', { q: query.trim() })}>
            {t('Try another name, or the plant family, such as Solanaceae.')}
          </EmptyState>
        </section>
      ) : (
        <ul
          className="card grid divide-y divide-line overflow-hidden p-0 lg:grid-cols-2 lg:divide-y-0"
          aria-label={t('Crops')}
        >
          {shown.map((c) => (
            <li key={c.slug} className="lg:border-b lg:border-line lg:odd:border-r">
              <Link to={`/crops/${c.slug}`} className="flex items-center gap-3 px-5 py-3 hover:bg-sunken">
                <span className="min-w-0 flex-1">
                  <span className="block font-semibold">{displayName(c)}</span>
                  <span className="block truncate text-sm text-muted">
                    <i>{c.scientific_name}</i>, {c.family}
                  </span>
                </span>
                <ChevronRight className="size-4 shrink-0 text-muted" aria-hidden />
              </Link>
            </li>
          ))}
        </ul>
      )}

      <p className="text-sm text-muted">
        <Link to="/crop-data" className="font-semibold text-leaf underline-offset-2 hover:underline">
          {t('Where the crop data comes from')}
        </Link>
      </p>
    </>
  )
}
