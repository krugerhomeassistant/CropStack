import { useEffect, useState } from 'react'
import { Link } from 'react-router'
import { BookOpen, ChartLine, ChevronRight, LogOut, Settings as SettingsIcon, Sparkles, Users } from 'lucide-react'
import { t } from '../i18n'
import { useApp } from '../state'
import { PageHeader } from '../components/ui'

const LINKS = [
  { to: '/crops', label: 'Crops', hint: 'Sowing, water and spacing for each crop, with sources', icon: BookOpen },
  { to: '/climate', label: 'Climate', hint: 'Temperatures, rain, frost and daylight through the year', icon: ChartLine },
  { to: '/ask', label: 'Ask', hint: 'Garden questions answered by the garden assistant', icon: Sparkles },
  { to: '/household', label: 'Household', hint: 'People, roles and invites', icon: Users },
  { to: '/settings', label: 'Settings', hint: 'Start screen, units and data sources', icon: SettingsIcon },
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
      <PageHeader title={t('More')} />
      <ul className="card flex flex-col divide-y divide-line overflow-hidden p-0">
        {LINKS.map(({ to, label, hint, icon: Icon }) => (
          <li key={to}>
            <Link to={to} className="flex items-center gap-3 px-5 py-4 hover:bg-sunken">
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
          <button className="flex w-full items-center gap-3 px-5 py-4 text-left hover:bg-sunken" onClick={logout}>
            <LogOut className="size-5 shrink-0 text-muted" aria-hidden />
            <span className="font-semibold">{t('Log out')}</span>
          </button>
        </li>
      </ul>
      {version && <p className="text-center text-xs text-muted">CropStack v{version}</p>}
    </>
  )
}
