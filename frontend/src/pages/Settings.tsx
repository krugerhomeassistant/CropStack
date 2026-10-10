import { useState } from 'react'
import { api, type Prefs } from '../api'
import AiSettings from '../components/AiSettings'
import DataSources from '../components/DataSources'
import { N_, t } from '../i18n'
import { ErrorMessage, PageHeader, RadioCards, Section } from '../components/ui'
import { useApp } from '../state'

const START = [
  { value: 'today', label: N_('Today'), hint: N_("What to do today: planting, watering, feeding, harvesting") },
  { value: 'garden', label: N_('Garden'), hint: N_('Your garden and its beds') },
  { value: 'climate', label: N_('Climate'), hint: N_('Temperatures, rain, frost and daylight') },
] as const

const UNITS = [
  { value: 'metric', label: N_('Metric'), hint: '°C, mm, m' },
  { value: 'imperial', label: N_('Imperial'), hint: '°F, in, ft' },
] as const

/** One preference as its own section; the section title is the radio group's visible label. */
function Choice<V extends string>(props: {
  legend: string
  name: string
  options: readonly { value: V; label: string; hint: string }[]
  value: V
  onChange: (v: V) => void
}) {
  return (
    <Section title={props.legend}>
      <RadioCards
        legend={props.legend}
        hideLegend
        name={props.name}
        options={props.options.map((o) => ({ ...o, label: t(o.label), hint: t(o.hint) }))}
        value={props.value}
        onChange={props.onChange}
      />
    </Section>
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
      <PageHeader
        title={t('Settings')}
        subtitle={t('These are yours only; everyone in the household chooses their own.')}
      />
      {error && <ErrorMessage>{error}</ErrorMessage>}
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
      <DataSources isOwner={user.role === 'owner'} />
      {user.role === 'owner' && <AiSettings />}
    </>
  )
}
