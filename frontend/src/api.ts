import type { Units } from './units'

export type Role = 'owner' | 'member' | 'viewer'

export type Prefs = { start: 'today' | 'garden' | 'climate'; units: Units }

export type User = {
  prefs: Prefs
  id: number
  username: string
  display_name: string
  created_at: string
  role: Role
  household: { id: number; name: string }
}

export type Member = { user_id: number; username: string; display_name: string; role: Role }
export type Household = { id: number; name: string; my_role: Role; members: Member[] }
export type InviteInfo = { household: string; role: Role; expires_at: string }
export type PendingInvite = { id: string; role: Role; created_at: string; expires_at: string }
export type NewInvite = PendingInvite & { token: string; path: string }

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
  last_spring_frost: string | null // "MM-DD", null when frost is rarer than the chosen risk
  first_fall_frost: string | null
  growing_season_days: number
  frost_free: boolean
  frost_years_pct: number
  frost_probability: number
  frost_nights_per_year: number
  zone: string
  extreme_min_c: number
  hottest_day_c: number | null
  daylight_hours: number[]
  monthly: { tmin: Monthly; tmax: Monthly; soil: Monthly; rain: Monthly; frost_nights: Monthly }
  annual_rain_mm: number
  rain_season: { start_month: number; end_month: number; share_pct: number } | null
  trend_per_decade: { tmin?: number; tmax?: number }
  elevation_m: number | null
  period: string
  source: string
}

export type DayWeather = {
  date: string
  tmin: number | null
  tmax: number | null
  precip: number | null
  precip_prob: number | null
  et0: number | null
  rh: number | null
  wind: number | null
  soil_t: number | null
  code: number | null
}

export type Weather = {
  today: DayWeather | null
  days: DayWeather[]
  recent: { days: number; temp_diff_c: number; rain_mm: number; rain_normal_mm: number; rain_percentile: number } | null
  timezone: string
  fetched_at: string
  stale: boolean
  source: string
}

export type HouseholdSettings = { forecast: boolean; place_search: boolean }
export type DataSource = {
  id: string
  name: string
  url: string
  sends: string
  when: string
  used_for: string
  licence: string
  switch: keyof HouseholdSettings | null
  enabled: boolean
}

// ---------------------------------------------------------------- catalog (SPEC §16.1: every value is cited)

export type Evidence =
  'peer-reviewed' | 'government' | 'extension-service' | 'model' | 'grower-reported' | 'traditional'
export type SourceRef = { ref: string; locator?: string | null; retrieved?: string | null; snapshot?: string | null }
export type Range = { min?: number | null; opt?: number | null; max?: number | null }
export type Fact = {
  value: number | string | boolean | Range
  unit?: string | null
  qualifiers?: Record<string, string | number | null>
  evidence: Evidence
  confidence: 'high' | 'medium' | 'low'
  estimate?: boolean
  sources: SourceRef[]
}
export type FactOrList = Fact | Fact[]
export type CatalogSource = {
  id: string
  title: string
  author: string | null
  url: string
  license: string
  use: 'bundle' | 'facts-only' | 'link-only'
  extra_terms: string | null
  tos_reviewed: string
}
export type CropSummary = { slug: string; names: Record<string, string[]>; scientific_name: string; family: string }
export type CropData = CropSummary & {
  rotation_group?: string | null
  life_cycle: 'annual' | 'biennial' | 'perennial'
  description?: string | null
  requirements?: Record<string, Record<string, FactOrList>>
  params?: Record<string, FactOrList>
}
export type CatalogItem<T> = { data: T; origin: string; sources: Record<string, CatalogSource> }

export class ApiError extends Error {
  constructor(
    public status: number,
    message: string,
  ) {
    super(message)
  }
}

async function request<T>(method: string, path: string, body?: unknown): Promise<T> {
  const resp = await fetch(`/api/v1${path}`, {
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
  register: (username: string, password: string, display_name = '', invite?: string) =>
    request<User>('POST', '/auth/register', { username, password, display_name, invite }),
  household: () => request<Household>('GET', '/household'),
  renameHousehold: (name: string) => request<{ name: string }>('PUT', '/household', { name }),
  setRole: (userId: number, role: Role) => request<{ role: Role }>('PUT', `/household/members/${userId}`, { role }),
  removeMember: (userId: number) => request<{ ok: boolean }>('DELETE', `/household/members/${userId}`),
  invites: () => request<PendingInvite[]>('GET', '/household/invites'),
  createInvite: (role: Role) => request<NewInvite>('POST', '/household/invites', { role }),
  revokeInvite: (id: string) => request<{ ok: boolean }>('DELETE', `/household/invites/${id}`),
  inviteInfo: (token: string) => request<InviteInfo>('GET', `/invites/${encodeURIComponent(token)}`),
  logout: () => request<{ ok: boolean }>('POST', '/auth/logout'),
  garden: () => request<Garden>('GET', '/sites/current'),
  saveGarden: (garden: GardenInput) => request<Garden>('PUT', '/sites/current', garden),
  climate: () => request<Climate>('GET', '/sites/current/climate'),
  savePrefs: (prefs: Prefs) => request<Prefs>('PUT', '/auth/prefs', prefs),
  weather: () => request<Weather>('GET', '/sites/current/weather'),
  householdSettings: () => request<HouseholdSettings>('GET', '/household/settings'),
  saveHouseholdSettings: (settings: HouseholdSettings) =>
    request<HouseholdSettings>('PUT', '/household/settings', settings),
  dataSources: () => request<DataSource[]>('GET', '/household/data-sources'),
  crops: () => request<CropSummary[]>('GET', '/catalog/crop'),
  crop: (slug: string) => request<CatalogItem<CropData>>('GET', `/catalog/crop/${encodeURIComponent(slug)}`),
  catalogSources: () => request<CatalogSource[]>('GET', '/catalog/sources'),
  places: (q: string) => request<Place[]>('GET', `/places?q=${encodeURIComponent(q)}`),
}
