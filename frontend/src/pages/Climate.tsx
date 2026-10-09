import { useState } from 'react'
import { type Climate as ClimateData } from '../api'
import ClimateCard from '../components/ClimateCard'
import ClimateCharts from '../components/ClimateCharts'
import { PageHeader } from '../components/ui'
import { t } from '../i18n'
import { useApp } from '../state'

export default function Climate() {
  const { garden, user } = useApp()
  // Charts wait for the summary: the first request downloads the weather record, and one request is enough.
  const [climate, setClimate] = useState<ClimateData | null>(null)
  return (
    <>
      <PageHeader title={t('Climate')} subtitle={t('What 30 years of weather records say about your garden.')} />
      <ClimateCard
        gardenKey={`${garden.latitude},${garden.longitude},${garden.frost_probability}`}
        units={user.prefs.units}
        onLoaded={setClimate}
      />
      {climate && <ClimateCharts climate={climate} units={user.prefs.units} />}
    </>
  )
}
