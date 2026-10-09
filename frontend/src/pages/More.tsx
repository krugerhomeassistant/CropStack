import { useEffect, useState } from 'react'
import { Link } from 'react-router'
import { ChartLine, ChevronRight, LogOut, Settings as SettingsIcon, Users } from 'lucide-react'
import { t } from '../i18n'
import { useApp } from '../state'

const LINKS = [
  { to: '/climate', label: 'Climate', hint: 'Temperatures, rain, frost and daylight through the year', icon: ChartLine },
  { to: '/household', label: 'Household', hint: 'People, roles and invites', icon: Users },
  { to: '/settings', label: 'Settings', hint: 'Start screen and units', icon: SettingsIcon },
]

export default function More() {
  const { logout } = useApp()
  const [version, setVersion] = useState('')

  useEffect(() => {
    fetch('/api/health')
      .then((r) => r.json())
      .then((h) => setVersion(h.version))
      .catch(() => {})
  }, [])

  return (
    <>
      <h1 className="text-2xl font-extrabold">{t('More')}</h1>
      <ul className="card flex flex-col divide-y divide-ink/10 p-0">
        {LINKS.map(({ to, label, hint, icon: Icon }) => (
          <li key={to}>
            <Link to={to} className="flex items-center gap-3 px-5 py-4">
              <Icon className="size-5 shrink-0 text-leaf" aria-hidden />
              <span className="flex-1">
                <span className="block font-semibold">{t(label)}</span>
                <span className="block text-sm text-muted">{t(hint)}</span>
              </span>
              <ChevronRight className="size-4 text-muted" aria-hidden />
            </Link>
          </li>
        ))}
        <li>
          <button className="flex w-full items-center gap-3 px-5 py-4 text-left" onClick={logout}>
            <LogOut className="size-5 shrink-0 text-muted" aria-hidden />
            <span className="font-semibold">{t('Log out')}</span>
          </button>
        </li>
      </ul>
      {version && <p className="text-center text-xs text-muted">CropStack v{version}</p>}
    </>
  )
}
