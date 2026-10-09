import { useEffect, useState } from 'react'
import { Sprout } from 'lucide-react'
import { api, ApiError, type Garden, type User } from './api'
import Auth from './pages/Auth'
import GardenSetup from './pages/GardenSetup'
import Home from './pages/Home'

type State =
  | { screen: 'loading' }
  | { screen: 'error' }
  | { screen: 'auth'; registrationOpen: boolean }
  | { screen: 'setup'; user: User; garden: Garden | null }
  | { screen: 'home'; user: User; garden: Garden }

export default function App() {
  const [state, setState] = useState<State>({ screen: 'loading' })

  async function load() {
    try {
      const status = await api.status()
      if (!status.authenticated) return setState({ screen: 'auth', registrationOpen: status.registration_open })
      const user = await api.me()
      const garden = await api.garden().catch((e) => {
        if (e instanceof ApiError && e.status === 404) return null
        throw e
      })
      setState(garden ? { screen: 'home', user, garden } : { screen: 'setup', user, garden: null })
    } catch {
      setState({ screen: 'error' })
    }
  }

  useEffect(() => {
    load()
  }, [])

  async function logout() {
    await api.logout()
    load()
  }

  switch (state.screen) {
    case 'loading':
    case 'error':
      return (
        <main className="mx-auto flex min-h-dvh max-w-md flex-col items-center justify-center gap-3 px-6 text-center">
          <Sprout className="size-12 text-leaf" aria-hidden />
          <p className="text-muted" role="status">
            {state.screen === 'error' ? 'Cannot reach the CropStack server.' : 'Loading…'}
          </p>
          {state.screen === 'error' && (
            <button className="btn" onClick={load}>
              Try again
            </button>
          )}
        </main>
      )
    case 'auth':
      return <Auth registrationOpen={state.registrationOpen} onDone={load} />
    case 'setup':
      return (
        <GardenSetup
          garden={state.garden}
          onSaved={(garden) => setState({ screen: 'home', user: state.user, garden })}
          onCancel={state.garden ? () => setState({ ...state, screen: 'home', garden: state.garden! }) : undefined}
        />
      )
    case 'home':
      return (
        <Home
          user={state.user}
          garden={state.garden}
          onEdit={() => setState({ screen: 'setup', user: state.user, garden: state.garden })}
          onLogout={logout}
        />
      )
  }
}
