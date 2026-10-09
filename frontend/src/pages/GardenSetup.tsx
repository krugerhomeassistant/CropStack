import { useState, type FormEvent } from 'react'
import { LocateFixed } from 'lucide-react'
import { api, type Garden, type GardenInput } from '../api'
import PlaceSearch from '../components/PlaceSearch'

type Props = { garden: Garden | null; onSaved: (garden: Garden) => void; onCancel?: () => void }

const FROST_CHOICES = [
  { value: 10, label: 'Cautious', hint: 'frost after the spring date in 1 year out of 10' },
  { value: 50, label: 'Typical', hint: 'the median frost date' },
  { value: 90, label: 'Bold', hint: 'plant early, accept more frost risk' },
]

export default function GardenSetup({ garden, onSaved, onCancel }: Props) {
  const [form, setForm] = useState({
    name: garden?.name ?? 'My garden',
    latitude: garden ? String(garden.latitude) : '',
    longitude: garden ? String(garden.longitude) : '',
    postal_code: garden?.postal_code ?? '',
    frost_probability: garden?.frost_probability ?? 50,
  })
  const [error, setError] = useState('')
  const [busy, setBusy] = useState(false)
  const set = (patch: Partial<typeof form>) => setForm({ ...form, ...patch })

  function locate() {
    setError('')
    if (!navigator.geolocation) return setError('Location is not available in this browser.')
    navigator.geolocation.getCurrentPosition(
      (pos) => set({ latitude: pos.coords.latitude.toFixed(4), longitude: pos.coords.longitude.toFixed(4) }),
      // Browsers only share location over HTTPS or localhost, so a LAN install (http://zima-ip) lands here.
      () => setError('Could not get your location. Enter it by hand (e.g. from Google Maps: right-click → coordinates).'),
    )
  }

  async function submit(e: FormEvent) {
    e.preventDefault()
    setBusy(true)
    setError('')
    const body: GardenInput = { ...form, latitude: Number(form.latitude), longitude: Number(form.longitude) }
    try {
      onSaved(await api.saveGarden(body))
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Something went wrong')
    } finally {
      setBusy(false)
    }
  }

  return (
    <main className="mx-auto flex min-h-dvh max-w-md flex-col gap-6 px-6 py-10">
      <header>
        <h1 className="text-2xl font-extrabold">{garden ? 'Edit your garden' : 'Where is your garden?'}</h1>
        <p className="text-muted">Your location sets your climate: hardiness zone, frost dates and daylight.</p>
      </header>

      <form className="card flex flex-col gap-4" onSubmit={submit}>
        <label className="field">
          <span>Garden name</span>
          <input
            className="input"
            required
            maxLength={80}
            value={form.name}
            onChange={(e) => set({ name: e.target.value })}
          />
        </label>

        <fieldset className="flex flex-col gap-2">
          <legend className="mb-2 text-sm font-semibold">Location</legend>
          <PlaceSearch
            onPick={(place) =>
              set({
                latitude: String(place.latitude),
                longitude: String(place.longitude),
                postal_code: place.postal_code || form.postal_code,
              })
            }
          />
          <button type="button" className="btn-secondary" onClick={locate}>
            <LocateFixed className="size-4" aria-hidden /> Use my current location
          </button>
          <div className="grid grid-cols-2 gap-3">
            <label className="field">
              <span>Latitude</span>
              <input
                className="input"
                inputMode="decimal"
                required
                type="number"
                step="any"
                min={-90}
                max={90}
                value={form.latitude}
                onChange={(e) => set({ latitude: e.target.value })}
              />
            </label>
            <label className="field">
              <span>Longitude</span>
              <input
                className="input"
                inputMode="decimal"
                required
                type="number"
                step="any"
                min={-180}
                max={180}
                value={form.longitude}
                onChange={(e) => set({ longitude: e.target.value })}
              />
            </label>
          </div>
          <label className="field">
            <span>Postal code (optional)</span>
            <input
              className="input"
              maxLength={16}
              value={form.postal_code}
              onChange={(e) => set({ postal_code: e.target.value })}
            />
          </label>
        </fieldset>

        <fieldset className="flex flex-col gap-2">
          <legend className="mb-2 text-sm font-semibold">Frost risk</legend>
          {FROST_CHOICES.map((c) => (
            <label key={c.value} className="flex items-start gap-3 rounded-xl border border-ink/10 p-3">
              <input
                type="radio"
                name="frost"
                className="mt-1 accent-leaf"
                checked={form.frost_probability === c.value}
                onChange={() => set({ frost_probability: c.value })}
              />
              <span>
                <span className="font-semibold">{c.label}</span>
                <span className="block text-sm text-muted">{c.hint}</span>
              </span>
            </label>
          ))}
        </fieldset>

        {error && (
          <p className="text-sm text-red-600" role="alert">
            {error}
          </p>
        )}
        <button className="btn" disabled={busy}>
          Save garden
        </button>
        {onCancel && (
          <button type="button" className="text-sm text-muted underline" onClick={onCancel}>
            Cancel
          </button>
        )}
      </form>
    </main>
  )
}
