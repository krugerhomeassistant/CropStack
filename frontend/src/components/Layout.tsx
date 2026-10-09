import { NavLink, Outlet } from 'react-router'
import { CalendarCheck, Menu, Sprout } from 'lucide-react'
import { t } from '../i18n'

// shortcut: only sections that exist get a tab; Calendar and Animals join when they have content (PLAN 7, 9).
const TABS = [
  { to: '/today', label: 'Today', icon: CalendarCheck },
  { to: '/garden', label: 'Garden', icon: Sprout },
  { to: '/more', label: 'More', icon: Menu },
]

export default function Layout() {
  return (
    <>
      <main className="mx-auto flex min-h-dvh max-w-md flex-col gap-6 px-6 pt-8 pb-[calc(var(--nav-h)+1.5rem)]">
        <Outlet />
      </main>
      <nav
        aria-label={t('Main')}
        className="fixed inset-x-0 bottom-0 z-10 border-t border-ink/10 bg-card pb-[env(safe-area-inset-bottom)]"
      >
        <ul className="mx-auto flex h-14 max-w-md">
          {TABS.map(({ to, label, icon: Icon }) => (
            <li key={to} className="flex-1">
              <NavLink
                to={to}
                className={({ isActive }) =>
                  `flex h-full flex-col items-center justify-center gap-0.5 text-xs font-semibold ${
                    isActive ? 'text-leaf' : 'text-muted'
                  }`
                }
              >
                <Icon className="size-5" aria-hidden />
                {t(label)}
              </NavLink>
            </li>
          ))}
        </ul>
      </nav>
    </>
  )
}
