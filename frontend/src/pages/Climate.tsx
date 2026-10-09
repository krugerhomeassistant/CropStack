import ClimateCard from '../components/ClimateCard'
import { t } from '../i18n'
import { useApp } from '../state'

export default function Climate() {
  const { garden, user } = useApp()
  return (
    <>
      <h1 className="text-2xl font-extrabold">{t('Climate')}</h1>
      {/* shortcut: v0.4 summary card until the chart-based climate explorer (PLAN Phase 11). */}
      <ClimateCard
        gardenKey={`${garden.latitude},${garden.longitude},${garden.frost_probability}`}
        units={user.prefs.units}
      />
    </>
  )
}
