import { useEffect, useState } from 'react'
import { Sprout } from 'lucide-react'
import { api, ApiError, type Garden, type User } from './api'
import Auth, { type Invite } from './pages/Auth'
import GardenSetup from './pages/GardenSetup'
import Home from './pages/Home'
import Household from './pages/Household'

const INVITE_PATH = /^\/invite\/([^/]+)$/

type State =
  | { screen: 'loading' }
  | { screen: 'error' }
  | { screen: 'auth'; registrationOpen: boolean; invite?: Invite; notice?: string }
  | { screen: 'setup'; user: User; garden: Garden | null }
  | { screen: 'waiting'; user: User }
  | { screen: 'home'; user: User; garden: Garden }
  | { screen: 'household'; user: User; garden: Garden | null }

export default function App() {
  const [state, setState] = useState<State>({ screen: 'loading' })

  async function load() {
    try {
      const status = await api.status()
      const token = INVITE_PATH.exec(location.pathname)?.[1]
      if (!status.authenticated) {
        if (!token) return setState({ screen: 'auth', registrationOpen: status.registration_open })
        const info = await api.inviteInfo(token).catch(() => null)
        return setState(
          info
            ? { screen: 'auth', registrationOpen: status.registration_open, invite: { ...info, token } }
            : { screen: 'auth', registrationOpen: status.registration_open, notice: 'This invite link has expired or was already used. Ask for a new one.' },
        )
      }
      if (token) history.replaceState(null, '', '/') // signed in: the invite was used (or isn't needed)
      const user = await api.me()
      const garden = await api.garden().catch((e) => {
        if (e instanceof ApiError && e.status === 404) return null
        throw e
      })
      if (garden) setState({ screen: 'home', user, garden })
      else setState(user.role === 'owner' ? { screen: 'setup', user, garden: null } : { screen: 'waiting', user })
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
      return (
        <Auth registrationOpen={state.registrationOpen} invite={state.invite} notice={state.notice} onDone={load} />
      )
    case 'waiting':
      return (
        <main className="mx-auto flex min-h-dvh max-w-md flex-col items-center justify-center gap-4 px-6 text-center">
          <Sprout className="size-12 text-leaf" aria-hidden />
          <h1 className="text-2xl font-extrabold">Welcome to {state.user.household.name}</h1>
          <p className="text-muted">The garden hasn't been set up yet. Once the owner adds it, your tasks appear here.</p>
          <button className="btn-secondary" onClick={load}>
            Check again
          </button>
          <button className="text-sm text-muted underline" onClick={logout}>
            Log out
          </button>
        </main>
      )
    case 'household':
      return (
        <Household
          user={state.user}
          onBack={() =>
            setState(state.garden ? { screen: 'home', user: state.user, garden: state.garden } : { screen: 'loading' })
          }
        />
      )
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
          onHousehold={() => setState({ screen: 'household', user: state.user, garden: state.garden })}
          onLogout={logout}
        />
      )
  }
}
