import { useState } from 'react'
import { Search } from 'lucide-react'
import { api, type Place } from '../api'
import { t } from '../i18n'

type Props = { onPick: (place: Place) => void }

/** Search on submit only: Nominatim's usage policy allows about one request per second. */
export default function PlaceSearch({ onPick }: Props) {
  const [query, setQuery] = useState('')
  const [results, setResults] = useState<Place[] | null>(null)
  const [error, setError] = useState('')
  const [busy, setBusy] = useState(false)

  // Not a <form>: it lives inside the garden form, and forms can't nest.
  async function search() {
    if (query.trim().length < 2) return setError(t('Type at least 2 characters.'))
    setBusy(true)
    setError('')
    try {
      setResults(await api.places(query.trim()))
    } catch (err) {
      setError(err instanceof Error ? err.message : t('Search failed'))
    } finally {
      setBusy(false)
    }
  }

  return (
    <div className="flex flex-col gap-2">
      <div className="flex gap-2" role="search">
        <label className="sr-only" htmlFor="place-query">
          {t('Town, address or postal code')}
        </label>
        <input
          id="place-query"
          className="input"
          placeholder={t('Town, address or postal code')}
          maxLength={120}
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          onKeyDown={(e) => {
            if (e.key === 'Enter') {
              e.preventDefault() // don't submit the garden form
              search()
            }
          }}
        />
        <button type="button" className="btn-secondary shrink-0" disabled={busy} aria-label={t('Search')} onClick={search}>
          <Search className="size-4" aria-hidden />
        </button>
      </div>
      {error && (
        <p className="text-sm text-red-600" role="alert">
          {error}
        </p>
      )}
      {results && (
        <ul className="flex flex-col gap-1" aria-label={t('Search results')}>
          {results.length === 0 && <li className="text-sm text-muted">{t('No places found. Try a nearby town.')}</li>}
          {results.map((place) => (
            <li key={`${place.latitude},${place.longitude}`}>
              <button
                type="button"
                className="w-full rounded-lg px-2 py-1.5 text-left text-sm hover:bg-leaf/10"
                onClick={() => {
                  onPick(place)
                  setResults(null)
                }}
              >
                {place.label}
              </button>
            </li>
          ))}
        </ul>
      )}
      <p className="text-xs text-muted">{t('Search by © OpenStreetMap contributors')}</p>
    </div>
  )
}
