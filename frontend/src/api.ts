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
  soil: '' | 'sandy' | 'loamy' | 'clay'
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

/** Typical value per day of the year (365 days, 29 Feb dropped): the middle value and the range of 8 years in 10. */
export type Bands = { var: string; p10: (number | null)[]; p50: (number | null)[]; p90: (number | null)[]; years: string }
export type SowWindow = {
  start: string
  end: string
  length_days: number
  all_year: boolean
  best_start: string
  best_end: string
  success: number
  days_to_maturity: { p10: number; p50: number; p90: number }
}
export type SowAnalysis = {
  windows: SowWindow[]
  success_by_day: number[]
  verdict: { state: 'yes' | 'risky' | 'no'; best_success: number; threshold: number; blockers: string[] }
}
export type CropWindows =
  | { slug: string; usable: false; missing: string[] }
  | ({
      slug: string
      usable: true
      estimates: string[]
      /** Seedlings raised indoors and set out; dates are set-out dates. */
      transplant?: SowAnalysis & { age_days: number }
    } & SowAnalysis)
export type PlantingStatus = 'planned' | 'sown' | 'germinated' | 'transplanted' | 'harvesting' | 'finished' | 'failed'
export type Planting = {
  id: number
  crop: string
  method: 'direct' | 'transplant'
  status: PlantingStatus
  start_date: string
  set_out_date: string | null
  quantity: number
  location: string
  bed_id: number | null
  cells: [number, number][]
  ends_on: string | null
  notes: string
  harvest_from?: string | null
  harvest_to?: string | null
  next_job?: { title: string; date: string } | null
}
export type PlantingIn = Pick<Planting, 'crop' | 'method' | 'start_date' | 'set_out_date' | 'location' | 'notes'> & {
  quantity?: number
  bed_id?: number | null
  cells?: [number, number][]
  ends_on?: string | null
}
export type BedKind = 'bed' | 'container' | 'row'
export type Bed = {
  id: number
  name: string
  kind: BedKind
  x: number
  y: number
  width: number
  length: number
  cell_cm: number
  layout: string
  cols: number
  outside: number
  rows: number
  placements: Placement[]
  clashes: { cell: [number, number]; plantings: [number, number] }[]
  over_capacity: number[]
  plantings: number[]
  area_m2: number
  needed_m2: number
  unknown_footprint: number
  crowded: boolean
}
export type BedIn = Pick<Bed, 'name' | 'kind' | 'x' | 'y' | 'width' | 'length' | 'cell_cm' | 'layout'>
export type Placement = {
  planting_id: number
  crop: string
  name: string
  cells: [number, number][]
  from: string
  until: string
  quantity: number
  method: 'direct' | 'transplant'
  start_date: string
  set_out_date: string | null
  capacity: number
  status: PlantingStatus
  harvest_from: string | null
  harvest_to: string | null
  next_job: { title: string; date: string } | null
}
export type Recommendation = {
  crop: string
  name: string
  method: 'direct' | 'transplant'
  state: 'now' | 'soon'
  start_date: string
  set_out_date: string | null
  from: string
  until: string
  best_from: string
  best_to: string
  all_year: boolean
  success: number
  age_days: number
  where: { bed_id: number; bed: string; cells: [number, number][]; free_cells: number; plants: number; same_family_before: boolean } | null
  harvest_from: string
  harvest_to: string
  family: string
  plants_per_cell: number
}
export type Recommendations = { garden: boolean; today?: string; has_beds?: boolean; now: Recommendation[]; soon: Recommendation[] }
export type Job = {
  id: number
  kind: 'sow' | 'set_out' | 'harvest' | 'frost' | 'heat' | 'water' | 'check'
  group: string
  title: string
  reason: string
  earliest: string
  ideal: string
  latest: string
  overdue: boolean
  planting_id: number | null
  steps: string[]
  watch: Watch[]
}
export type Watch = { slug: string; name: string; type: string; identify: string; verdict: string; action: string }
export type TodayData = { date: string; groups: { group: string; tasks: Job[] }[]; upcoming: Job[] }
export type HarvestUnit = 'kg' | 'g' | 'count' | 'bunch'
export type Harvest = { id: number; planting_id: number; harvested_on: string; quantity: number; unit: HarvestUnit; notes: string }
export type Probability = { var: string; days: number[]; years: string }

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

export type CalendarEvent = { date: string; kind: 'sow' | 'set_out' | 'harvest'; title: string; done: boolean; planting_id: number | null }
export type AiProvider = 'anthropic' | 'openai' | 'openrouter' | 'ollama' | 'custom'
export type AiConfig = {
  configured: boolean
  provider: AiProvider | ''
  base_url: string
  model: string
  has_key: boolean
  key_hint: string
  providers: Record<AiProvider, { base_url: string; model: string }>
}
export type AiIn = { provider: AiProvider; base_url: string; model: string; api_key?: string | null }
export type Turn = { role: 'user' | 'assistant'; content: string }

// ---------------------------------------------------------------- catalog (SPEC §16.1: every value is cited)

export type Evidence =
  'peer-reviewed' | 'government' | 'extension-service' | 'model' | 'grower-reported' | 'traditional'
export type SourceRef = { ref: string; locator?: string | null; retrieved?: string | null; snapshot?: string | null }
export type Range = {
  min?: number | null
  opt_min?: number | null
  opt?: number | null
  opt_max?: number | null
  max?: number | null
}
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
    throw new ApiError(resp.status, message || `Request failed (${resp.status})`)
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
  bands: (name: string) => request<Bands>('GET', `/sites/current/climate/bands?var=${name}`),
  probability: (name: string, op: 'le' | 'ge', x: number) =>
    request<Probability>('GET', `/sites/current/climate/probability?var=${name}&op=${op}&x=${x}`),
  cropWindows: (slug: string) => request<CropWindows>('GET', `/crops/${encodeURIComponent(slug)}/windows`),
  today: () => request<TodayData>('GET', '/today'),
  finishJob: (id: number, status: 'done' | 'skipped') => request<Job>('PATCH', `/tasks/${id}`, { status }),
  plantings: () => request<Planting[]>('GET', '/plantings'),
  addPlanting: (body: PlantingIn) => request<Planting>('POST', '/plantings', body),
  updatePlanting: (id: number, body: Partial<Pick<Planting, 'status' | 'start_date' | 'set_out_date' | 'quantity' | 'location' | 'bed_id' | 'cells' | 'ends_on' | 'notes'>>) =>
    request<Planting>('PATCH', `/plantings/${id}`, body),
  deletePlanting: (id: number) => request<null>('DELETE', `/plantings/${id}`),
  recommendations: () => request<Recommendations>('GET', '/recommendations'),
  beds: () => request<Bed[]>('GET', '/beds'),
  addBed: (body: BedIn) => request<Bed>('POST', '/beds', body),
  updateBed: (id: number, body: Partial<BedIn>) => request<Bed>('PATCH', `/beds/${id}`, body),
  deleteBed: (id: number) => request<null>('DELETE', `/beds/${id}`),
  harvests: () => request<Harvest[]>('GET', '/plantings/harvests'),
  addHarvest: (plantingId: number, body: Omit<Harvest, 'id' | 'planting_id'>) =>
    request<Harvest>('POST', `/plantings/${plantingId}/harvests`, body),
  savePrefs: (prefs: Prefs) => request<Prefs>('PUT', '/auth/prefs', prefs),
  weather: () => request<Weather>('GET', '/sites/current/weather'),
  householdSettings: () => request<HouseholdSettings>('GET', '/household/settings'),
  saveHouseholdSettings: (settings: HouseholdSettings) =>
    request<HouseholdSettings>('PUT', '/household/settings', settings),
  calendar: (start: string, end: string) =>
    request<CalendarEvent[]>('GET', `/calendar?start=${start}&end=${end}`),
  ai: () => request<AiConfig>('GET', '/ai'),
  saveAi: (body: AiIn) => request<AiConfig>('PUT', '/ai', body),
  clearAi: () => request<AiConfig>('DELETE', '/ai'),
  testAi: (body: AiIn) => request<{ ok: boolean; reply?: string; error?: string }>('POST', '/ai/test', body),
  askAi: (messages: Turn[]) => request<{ reply: string }>('POST', '/ai/ask', { messages }),
  dataSources: () => request<DataSource[]>('GET', '/household/data-sources'),
  crops: () => request<CropSummary[]>('GET', '/catalog/crop'),
  crop: (slug: string) => request<CatalogItem<CropData>>('GET', `/catalog/crop/${encodeURIComponent(slug)}`),
  catalogSources: () => request<CatalogSource[]>('GET', '/catalog/sources'),
  places: (q: string) => request<Place[]>('GET', `/places?q=${encodeURIComponent(q)}`),
}
