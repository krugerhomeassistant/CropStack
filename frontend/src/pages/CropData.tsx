import { useEffect, useState } from 'react'
import { ExternalLink } from 'lucide-react'
import { api, type CatalogSource } from '../api'
import { ErrorState, PageHeader, Section, Skeleton } from '../components/ui'
import { N_, t } from '../i18n'

const USE: Record<CatalogSource['use'], { title: string; body: string }> = {
  bundle: {
    title: N_('Included in CropStack'),
    body: N_('Openly licensed. Values from these sources ship with CropStack, with credit.'),
  },
  'facts-only': {
    title: N_('Cited facts'),
    body: N_(
      'Copyrighted. CropStack stores single cited numbers from them and never copies their text, tables or images.',
    ),
  },
  'link-only': {
    title: N_('Further reading'),
    body: N_('Licences that do not allow reuse. CropStack links to them but takes no data from them.'),
  },
}

/** Credits for the crop catalog: every source with its licence (CC attribution practice for many-source works). */
export default function CropData() {
  const [sources, setSources] = useState<CatalogSource[] | null>(null)
  const [error, setError] = useState('')

  function load() {
    setError('')
    api.catalogSources().then(setSources, (e) => setError(e instanceof Error ? e.message : t('Failed to load')))
  }
  useEffect(load, [])

  return (
    <>
      <PageHeader
        back
        title={t('Where the crop data comes from')}
        subtitle={t(
          'Every value in the crop catalog cites its source and how strong the evidence is. The catalog is shared under CC BY-SA 4.0.',
        )}
      />
      {error && (
        <section className="card">
          <ErrorState message={error} onRetry={load} />
        </section>
      )}
      {!sources && !error && <Skeleton className="h-64" />}
      {sources &&
        (Object.keys(USE) as CatalogSource['use'][]).map((use) => {
          const group = sources.filter((s) => s.use === use).sort((a, b) => a.title.localeCompare(b.title))
          if (!group.length) return null
          return (
            <Section key={use} title={t(USE[use].title)} description={t(USE[use].body)}>
              <ul className="-my-3 divide-y divide-line">
                {group.map((s) => (
                  <li key={s.id} className="py-3">
                    <a href={s.url} target="_blank" rel="noreferrer" className="font-semibold hover:underline">
                      {s.title}
                      <ExternalLink className="ml-1 inline size-3 align-baseline" aria-hidden />
                    </a>
                    {s.author && <p className="text-sm text-muted">{s.author}</p>}
                    <p className="text-sm text-muted">{t('Licence: {licence}', { licence: s.license })}</p>
                    {s.extra_terms && <p className="text-sm text-muted">{s.extra_terms}</p>}
                  </li>
                ))}
              </ul>
            </Section>
          )
        })}
    </>
  )
}
