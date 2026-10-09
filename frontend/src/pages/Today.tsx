import { ListTodo } from 'lucide-react'
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
      <header>
        <p className="text-sm text-muted">
          {now.toLocaleDateString(undefined, { weekday: 'long', day: 'numeric', month: 'long' })} · {garden.name}
        </p>
        <h1 className="text-2xl font-extrabold">
          {greeting(now.getHours())}, {user.display_name || user.username}
        </h1>
      </header>

      <WeatherCard units={user.prefs.units} />

      {/* shortcut: placeholder until the task engine exists (PLAN Phase 6-7); keeps Today as the home screen. */}
      <section className="card flex flex-col items-center gap-3 py-8 text-center">
        <ListTodo className="size-10 text-leaf" aria-hidden />
        <h2 className="text-lg font-bold">{t('Your daily jobs will appear here')}</h2>
        <p className="text-sm text-muted">
          {t(
            'What to plant, water, feed and harvest, what to look out for, and how to do each job. They arrive with the crop planner, coming next.',
          )}
        </p>
      </section>
    </>
  )
}
