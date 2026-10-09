export type User = { id: number; username: string; display_name: string; created_at: string }

export type Garden = {
  id: number
  name: string
  latitude: number
  longitude: number
  postal_code: string
  frost_probability: number
}

export type GardenInput = Omit<Garden, 'id'>

export type Place = { label: string; latitude: number; longitude: number; postal_code: string }

type Monthly = (number | null)[]

export type Climate = {
  last_spring_frost: string | null // "MM-DD"
  first_fall_frost: string | null
  growing_season_days: number
  frost_free: boolean
  frost_years_pct: number
  frost_probability: number
  zone: string
  extreme_min_c: number
  daylight_hours: number[]
  monthly: { tmin: Monthly; tmax: Monthly; soil: Monthly; rain: Monthly; hot_days: Monthly }
  rainfall_regime: 'winter' | 'summer' | 'year-round' | 'dry'
  annual_rain_mm: number
  hot_days_per_year: number
  elevation_m: number | null
  period: string
  southern_hemisphere: boolean
  source: string
}

export class ApiError extends Error {
  constructor(
    public status: number,
    message: string,
  ) {
    super(message)
  }
}

async function request<T>(method: string, path: string, body?: unknown): Promise<T> {
  const resp = await fetch(`/api${path}`, {
    method,
    headers: body === undefined ? undefined : { 'Content-Type': 'application/json' },
    body: body === undefined ? undefined : JSON.stringify(body),
  })
  const data = await resp.json().catch(() => null)
  if (!resp.ok) {
    // FastAPI sends a string for HTTPException and a list of field errors for validation failures
    const detail = data?.detail
    const message = typeof detail === 'string' ? detail : Array.isArray(detail) ? detail[0]?.msg : resp.statusText
    throw new ApiError(resp.status, message || 'Request failed')
  }
  return data as T
}

export const api = {
  status: () => request<{ registration_open: boolean; authenticated: boolean }>('GET', '/auth/status'),
  me: () => request<User>('GET', '/auth/me'),
  login: (username: string, password: string) => request<User>('POST', '/auth/login', { username, password }),
  register: (username: string, password: string) => request<User>('POST', '/auth/register', { username, password }),
  logout: () => request<{ ok: boolean }>('POST', '/auth/logout'),
  garden: () => request<Garden>('GET', '/garden'),
  saveGarden: (garden: GardenInput) => request<Garden>('PUT', '/garden', garden),
  climate: () => request<Climate>('GET', '/garden/climate'),
  places: (q: string) => request<Place[]>('GET', `/places?q=${encodeURIComponent(q)}`),
}
