import { useState } from 'react'
import { api, type Prefs } from '../api'
import { N_, t } from '../i18n'
import { useApp } from '../state'

const START = [
  { value: 'today', label: N_('Today'), hint: N_("What to do today: planting, watering, feeding, harvesting") },
  { value: 'garden', label: N_('Garden'), hint: N_('Your garden and its beds') },
  { value: 'climate', label: N_('Climate'), hint: N_('Temperatures, rain, frost and daylight') },
] as const

const UNITS = [
  { value: 'metric', label: N_('Metric'), hint: '°C · mm · m' },
  { value: 'imperial', label: N_('Imperial'), hint: '°F · in · ft' },
] as const

function Choice<V extends string>(props: {
  legend: string
  name: string
  options: readonly { value: V; label: string; hint: string }[]
  value: V
  onChange: (v: V) => void
}) {
  return (
    <fieldset className="card flex flex-col gap-2">
      <legend className="float-left mb-2 font-bold">{props.legend}</legend>
      {props.options.map((o) => (
        <label key={o.value} className="flex items-start gap-3 rounded-xl border border-ink/10 p-3">
          <input
            type="radio"
            name={props.name}
            className="mt-1 accent-leaf"
            checked={props.value === o.value}
            onChange={() => props.onChange(o.value)}
          />
          <span>
            <span className="font-semibold">{t(o.label)}</span>
            <span className="block text-sm text-muted">{t(o.hint)}</span>
          </span>
        </label>
      ))}
    </fieldset>
  )
}

export default function Settings() {
  const { user, reload } = useApp()
  const [prefs, setPrefs] = useState(user.prefs) // shown immediately; the server copy follows
  const [error, setError] = useState('')

  async function save(patch: Partial<Prefs>) {
    const next = { ...prefs, ...patch }
    setPrefs(next)
    setError('')
    try {
      await api.savePrefs(next)
      await reload()
    } catch (err) {
      setPrefs(prefs)
      setError(err instanceof Error ? err.message : t('Something went wrong'))
    }
  }

  return (
    <>
      <h1 className="text-2xl font-extrabold">{t('Settings')}</h1>
      <p className="-mt-4 text-sm text-muted">{t('These are yours only; everyone in the household chooses their own.')}</p>
      {error && (
        <p className="text-sm text-red-600" role="alert">
          {error}
        </p>
      )}
      <Choice
        legend={t('Open the app on')}
        name="start"
        options={START}
        value={prefs.start}
        onChange={(start) => save({ start })}
      />
      <Choice
        legend={t('Units')}
        name="units"
        options={UNITS}
        value={prefs.units}
        onChange={(units) => save({ units })}
      />
    </>
  )
}
