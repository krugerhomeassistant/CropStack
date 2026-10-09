import ClimateCard from '../components/ClimateCard'
import { t } from '../i18n'
import { useApp } from '../state'
import { PageHeader } from '../components/ui'

export default function Climate() {
  const { garden, user } = useApp()
  return (
    <>
      <PageHeader title={t('Climate')} subtitle={t('What 30 years of weather records say about your garden.')} />
      {/* shortcut: v0.4 summary card until the chart-based climate explorer (PLAN Phase 11). */}
      <ClimateCard
        gardenKey={`${garden.latitude},${garden.longitude},${garden.frost_probability}`}
        units={user.prefs.units}
      />
    </>
  )
}
