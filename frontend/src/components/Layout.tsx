import { NavLink, Outlet } from 'react-router'
import { CalendarCheck, ChartLine, LogOut, Menu, Settings, Sprout, Users, type LucideIcon } from 'lucide-react'
import { t } from '../i18n'
import { useApp } from '../state'

type Dest = { to: string; label: string; icon: LucideIcon }

// shortcut: only sections that exist get a tab; Calendar and Animals join when they have content (PLAN 7, 9).
const MAIN: Dest[] = [
  { to: '/today', label: 'Today', icon: CalendarCheck },
  { to: '/garden', label: 'Garden', icon: Sprout },
]
/** Behind "More" on a phone; listed in full in the desktop rail. */
export const MORE: Dest[] = [
  { to: '/climate', label: 'Climate', icon: ChartLine },
  { to: '/household', label: 'Household', icon: Users },
  { to: '/settings', label: 'Settings', icon: Settings },
]

function RailLink({ to, label, icon: Icon }: Dest) {
  return (
    <NavLink
      to={to}
      className={({ isActive }) =>
        `flex min-h-11 items-center gap-3 rounded-[var(--radius-row)] px-3 font-semibold transition-colors ${
          isActive ? 'bg-leaf/12 text-leaf' : 'text-muted hover:bg-sunken hover:text-ink'
        }`
      }
    >
      <Icon className="size-5" aria-hidden />
      {t(label)}
    </NavLink>
  )
}

export default function Layout() {
  const { logout } = useApp()
  return (
    <>
      <nav
        aria-label={t('Main')}
        className="fixed inset-y-0 left-0 hidden w-60 flex-col gap-1 border-r border-line bg-surface px-4 py-6 lg:flex"
      >
        <p className="mb-6 px-3 font-display text-2xl font-extrabold text-leaf">CropStack</p>
        {[...MAIN, ...MORE].map((d) => (
          <RailLink key={d.to} {...d} />
        ))}
        <button
          type="button"
          onClick={logout}
          className="mt-auto flex min-h-11 items-center gap-3 rounded-[var(--radius-row)] px-3 font-semibold text-muted hover:bg-sunken hover:text-ink"
        >
          <LogOut className="size-5" aria-hidden />
          {t('Log out')}
        </button>
        <p className="px-3 pt-2 text-xs text-muted">CropStack v{__APP_VERSION__}</p>
      </nav>

      <main className="mx-auto flex min-h-dvh max-w-2xl flex-col gap-6 px-4 pt-8 pb-[calc(var(--nav-h)+1.5rem)] sm:px-8 lg:ml-60 lg:max-w-none lg:pb-12">
        <div className="mx-auto flex w-full max-w-[60rem] flex-col gap-6">
          <Outlet />
        </div>
      </main>

      <nav
        aria-label={t('Main')}
        className="fixed inset-x-0 bottom-0 z-10 border-t border-line bg-surface pb-[env(safe-area-inset-bottom)] shadow-[0_-4px_16px_rgb(0_0_0/0.06)] lg:hidden"
      >
        <ul className="mx-auto flex h-15 max-w-2xl">
          {[...MAIN, { to: '/more', label: 'More', icon: Menu }].map(({ to, label, icon: Icon }) => (
            <li key={to} className="flex-1">
              <NavLink
                to={to}
                className={({ isActive }) =>
                  `flex h-full flex-col items-center justify-center gap-0.5 text-xs font-semibold ${
                    isActive ? 'text-leaf' : 'text-muted'
                  }`
                }
              >
                <Icon className="size-6" aria-hidden />
                {t(label)}
              </NavLink>
            </li>
          ))}
        </ul>
      </nav>
    </>
  )
}
