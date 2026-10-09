import { createContext, useContext } from 'react'
import type { Garden, User } from './api'

export type AppState = {
  user: User
  garden: Garden
  setGarden: (garden: Garden) => void
  reload: () => Promise<void>
  logout: () => Promise<void>
}

export const AppContext = createContext<AppState | null>(null)

/** Signed-in state; only used inside the layout, which renders after user and garden are loaded. */
export function useApp(): AppState {
  const state = useContext(AppContext)
  if (!state) throw new Error('useApp outside AppContext')
  return state
}
