import Jobs from '../components/Jobs'
import { PageHeader } from '../components/ui'
import WeatherCard from '../components/WeatherCard'
import { t } from '../i18n'
import { useApp } from '../state'

function greeting(hour: number): string {
  if (hour < 12) return t('Good morning')
  if (hour < 18) return t('Good afternoon')
  return t('Good evening')
}

export default function Today() {
  const { user, garden } = useApp()
  const now = new Date()
  return (
    <>
      <PageHeader
        title={`${greeting(now.getHours())}, ${user.display_name || user.username}`}
        subtitle={t('{date} in {garden}', {
          date: now.toLocaleDateString(undefined, { weekday: 'long', day: 'numeric', month: 'long' }),
          garden: garden.name,
        })}
      />

      {/* Phone: weather first, then jobs. Desktop: jobs | weather (DESIGN.md, Layout). */}
      <div className="flex flex-col gap-6 lg:grid lg:grid-cols-[minmax(0,1fr)_22rem] lg:items-start">
        <div className="lg:order-2">
          <WeatherCard units={user.prefs.units} />
        </div>
        <Jobs />
      </div>
    </>
  )
}
