import { useEffect, useState } from 'react'
import { Navigate, Route, Routes } from 'react-router'
import { Sprout } from 'lucide-react'
import { api, ApiError, type Garden, type User } from './api'
import Layout from './components/Layout'
import { t } from './i18n'
import Auth, { type Invite } from './pages/Auth'
import Climate from './pages/Climate'
import GardenPage from './pages/Garden'
import GardenSetup from './pages/GardenSetup'
import Household from './pages/Household'
import More from './pages/More'
import Settings from './pages/Settings'
import Today from './pages/Today'
import { AppContext } from './state'

const INVITE_PATH = /^\/invite\/([^/]+)$/

/**
 * Why did loading fail? After an update the browser can still run the previous app from its offline cache for a
 * moment; it then calls API paths the new server no longer has. If the server is up and newer than this app,
 * reload once (per server version, so it can't loop) to pick up the new app. Returns an error to show otherwise.
 */
async function diagnose(error: unknown): Promise<string | null> {
  const health = await fetch('/api/health')
    .then((r) => (r.ok ? r.json() : null))
    .catch(() => null)
  if (!health) return t('Cannot reach the CropStack server.')
  if (health.version !== __APP_VERSION__) {
    const key = `reloaded-for-${health.version}`
    let already = false
    try {
      already = sessionStorage.getItem(key) === '1'
      sessionStorage.setItem(key, '1')
    } catch {
      // storage blocked: reload anyway; worst case the error below shows after a second failure
    }
    if (!already) {
      location.reload()
      return null
    }
  }
  return error instanceof Error ? error.message : t('Something went wrong')
}

type State =
  | { screen: 'loading' }
  | { screen: 'error'; message: string }
  | { screen: 'auth'; registrationOpen: boolean; invite?: Invite; notice?: string }
  | { screen: 'setup'; user: User }
  | { screen: 'waiting'; user: User }
  | { screen: 'app'; user: User; garden: Garden }

export default function App() {
  const [state, setState] = useState<State>({ screen: 'loading' })

  async function load() {
    try {
      const status = await api.status()
      const token = INVITE_PATH.exec(location.pathname)?.[1]
      if (!status.authenticated) {
        const open = status.registration_open
        if (!token) return setState({ screen: 'auth', registrationOpen: open })
        const info = await api.inviteInfo(token).catch(() => null)
        return setState(
          info
            ? { screen: 'auth', registrationOpen: open, invite: { ...info, token } }
            : {
                screen: 'auth',
                registrationOpen: open,
                notice: t('This invite link has expired or was already used. Ask for a new one.'),
              },
        )
      }
      const user = await api.me()
      const garden = await api.garden().catch((e) => {
        if (e instanceof ApiError && e.status === 404) return null
        throw e
      })
      if (garden) setState({ screen: 'app', user, garden })
      else setState(user.role === 'owner' ? { screen: 'setup', user } : { screen: 'waiting', user })
    } catch (error) {
      const message = await diagnose(error)
      if (message) setState({ screen: 'error', message })
    }
  }

  useEffect(() => {
    load()
  }, [])

  async function logout() {
    await api.logout()
    history.replaceState(null, '', '/')
    await load()
  }

  switch (state.screen) {
    case 'loading':
    case 'error':
      return (
        <main className="mx-auto flex min-h-dvh max-w-md flex-col items-center justify-center gap-3 px-6 text-center">
          <Sprout className="size-12 text-leaf" aria-hidden />
          <p className="text-muted" role="status">
            {state.screen === 'error' ? state.message : t('Loading…')}
          </p>
          {state.screen === 'error' && (
            // A full reload, not just a retry: it also picks up a newer app version.
            <button className="btn" onClick={() => location.reload()}>
              {t('Try again')}
            </button>
          )}
        </main>
      )
    case 'auth':
      return (
        <Auth registrationOpen={state.registrationOpen} invite={state.invite} notice={state.notice} onDone={load} />
      )
    case 'setup':
      return (
        <main className="mx-auto flex min-h-dvh max-w-md flex-col gap-6 px-6 py-10">
          <GardenSetup garden={null} onSaved={(garden) => setState({ screen: 'app', user: state.user, garden })} />
        </main>
      )
    case 'waiting':
      return (
        <main className="mx-auto flex min-h-dvh max-w-md flex-col items-center justify-center gap-4 px-6 text-center">
          <Sprout className="size-12 text-leaf" aria-hidden />
          <h1 className="text-2xl font-extrabold">{t('Welcome to {name}', { name: state.user.household.name })}</h1>
          <p className="text-muted">
            {t("The garden hasn't been set up yet. Once the owner adds it, your tasks appear here.")}
          </p>
          <button className="btn-secondary" onClick={load}>
            {t('Check again')}
          </button>
          <button className="text-sm text-muted underline" onClick={logout}>
            {t('Log out')}
          </button>
        </main>
      )
    case 'app': {
      const app = {
        user: state.user,
        garden: state.garden,
        setGarden: (garden: Garden) => setState({ ...state, garden }),
        reload: load,
        logout,
      }
      return (
        <AppContext.Provider value={app}>
          <Routes>
            <Route element={<Layout />}>
              <Route path="/today" element={<Today />} />
              <Route path="/garden" element={<GardenPage />} />
              <Route path="/more" element={<More />} />
              <Route path="/climate" element={<Climate />} />
              <Route path="/household" element={<Household />} />
              <Route path="/settings" element={<Settings />} />
            </Route>
            {/* "/", a used invite link, or anything unknown: the person's own start screen */}
            <Route path="*" element={<Navigate to={`/${state.user.prefs.start}`} replace />} />
          </Routes>
        </AppContext.Provider>
      )
    }
  }
}
