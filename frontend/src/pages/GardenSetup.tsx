import { useEffect, useState, type FormEvent } from 'react'
import { LocateFixed } from 'lucide-react'
import { api, type Garden, type GardenInput } from '../api'
import PlaceSearch from '../components/PlaceSearch'
import { N_, t } from '../i18n'
import { Button, ErrorMessage, PageHeader, RadioCards } from '../components/ui'

type Props = { garden: Garden | null; onSaved: (garden: Garden) => void; onCancel?: () => void }

const FROST_CHOICES = [
  { value: 10, label: N_('Cautious'), hint: N_('frost after the spring date in 1 year out of 10') },
  { value: 50, label: N_('Typical'), hint: N_('the median frost date') },
  { value: 90, label: N_('Bold'), hint: N_('plant early, accept more frost risk') },
]

const SOIL_CHOICES = [
  { value: 'sandy', label: N_('Sandy'), hint: N_('gritty, falls apart when rubbed, water drains away fast') },
  { value: 'loamy', label: N_('Silty or loamy'), hint: N_('smooth or crumbly, holds a shape briefly when squeezed') },
  { value: 'clay', label: N_('Clay'), hint: N_('sticky when wet, rolls into a ribbon, slow to drain') },
  { value: '', label: N_('Not sure'), hint: N_('uses a middle value; you can change it later') },
] as const

export default function GardenSetup({ garden, onSaved, onCancel }: Props) {
  const [form, setForm] = useState({
    name: garden?.name ?? 'My garden',
    latitude: garden ? String(garden.latitude) : '',
    longitude: garden ? String(garden.longitude) : '',
    postal_code: garden?.postal_code ?? '',
    frost_probability: garden?.frost_probability ?? 50,
    soil: garden?.soil ?? '',
  })
  const [error, setError] = useState('')
  const [busy, setBusy] = useState(false)
  const set = (patch: Partial<typeof form>) => setForm({ ...form, ...patch })
  const [placeSearch, setPlaceSearch] = useState<boolean | null>(null) // unknown until loaded: no flicker

  useEffect(() => {
    api.householdSettings().then((s) => setPlaceSearch(s.place_search), () => setPlaceSearch(true))
  }, [])

  function locate() {
    setError('')
    if (!navigator.geolocation) return setError(t('Location is not available in this browser.'))
    navigator.geolocation.getCurrentPosition(
      (pos) => set({ latitude: pos.coords.latitude.toFixed(4), longitude: pos.coords.longitude.toFixed(4) }),
      // Browsers only share location over HTTPS or localhost, so a LAN install (http://zima-ip) lands here.
      () => setError(t('Could not get your location. Enter it by hand (e.g. from Google Maps: right-click → coordinates).')),
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
      setError(err instanceof Error ? err.message : t('Something went wrong'))
    } finally {
      setBusy(false)
    }
  }

  return (
    <div className="flex flex-col gap-6">
      <PageHeader
        title={garden ? t('Edit your garden') : t('Where is your garden?')}
        subtitle={t('Your location sets your climate: temperatures, rain, frost and daylight.')}
      />

      <form className="card flex flex-col gap-4" onSubmit={submit}>
        <label className="field">
          <span>{t('Garden name')}</span>
          <input
            className="input"
            required
            maxLength={80}
            value={form.name}
            onChange={(e) => set({ name: e.target.value })}
          />
        </label>

        <fieldset className="flex flex-col gap-2">
          <legend className="mb-2 text-sm font-semibold">{t('Location')}</legend>
          {placeSearch === true && <PlaceSearch
            onPick={(place) =>
              set({
                latitude: String(place.latitude),
                longitude: String(place.longitude),
                postal_code: place.postal_code || form.postal_code,
              })
            }
          />}
          <Button variant="secondary" onClick={locate}>
            <LocateFixed className="size-4" aria-hidden /> {t('Use my current location')}
          </Button>
          <div className="grid grid-cols-2 gap-3">
            <label className="field">
              <span>{t('Latitude')}</span>
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
              <span>{t('Longitude')}</span>
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
            <span>{t('Postal code (optional)')}</span>
            <input
              className="input"
              maxLength={16}
              value={form.postal_code}
              onChange={(e) => set({ postal_code: e.target.value })}
            />
          </label>
        </fieldset>

        <RadioCards
          legend={t('Frost risk')}
          name="frost"
          options={FROST_CHOICES.map((c) => ({ ...c, label: t(c.label), hint: t(c.hint) }))}
          value={form.frost_probability}
          onChange={(frost_probability) => set({ frost_probability })}
        />

        <RadioCards
          legend={t('Soil')}
          name="soil"
          options={SOIL_CHOICES.map((c) => ({ ...c, label: t(c.label), hint: t(c.hint) }))}
          value={form.soil}
          onChange={(soil) => set({ soil })}
        />

        {error && <ErrorMessage>{error}</ErrorMessage>}
        <div className="flex flex-wrap gap-2">
          <Button type="submit" disabled={busy}>
            {t('Save garden')}
          </Button>
          {onCancel && (
            <Button variant="ghost" onClick={onCancel}>
              {t('Cancel')}
            </Button>
          )}
        </div>
      </form>
    </div>
  )
}
