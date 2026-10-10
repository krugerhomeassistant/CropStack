import { useEffect, useState } from 'react'
import { useSearchParams } from 'react-router'
import { MapPin, Pencil } from 'lucide-react'
import { api, type Recommendations as Recs } from '../api'
import { IconButton, Section, Tabs } from '../components/ui'
import { t } from '../i18n'
import { useApp } from '../state'
import CalendarTab from '../components/CalendarTab'
import LayoutEditor from '../components/LayoutEditor'
import Plantings from '../components/Plantings'
import Recommendations, { type PlantRequest } from '../components/Recommendations'
import GardenSetup from './GardenSetup'

const TABS = ['plan', 'plant', 'calendar', 'plantings'] as const
type Tab = (typeof TABS)[number]

/** The garden in four windows: the plan to draw and plant on, what to plant, a calendar, and the list of plantings. */
export default function GardenPage() {
  const { user, garden, setGarden } = useApp()
  const [editing, setEditing] = useState(false)
  const [params, setParams] = useSearchParams()
  const asked = params.get('tab')
  const tab: Tab = TABS.find((x) => x === asked) ?? 'plan'
  const [rev, setRev] = useState(0) // bumped when the plan changes so the plantings list reloads
  const [planRev, setPlanRev] = useState(0) // and the other way round
  const [recs, setRecs] = useState<Recs | null>(null)
  const [recsError, setRecsError] = useState('')
  const [request, setRequest] = useState<PlantRequest | null>(null)

  const loadRecs = () => {
    setRecsError('')
    api.recommendations().then(setRecs, (e) => setRecsError(e instanceof Error ? e.message : t('Failed to load')))
  }
  useEffect(loadRecs, [])
  const go = (next: Tab) => {
    setParams(next === 'plan' ? {} : { tab: next }, { replace: true })
    if (next === 'plant') loadRecs() // free cells change as beds fill
  }

  if (editing)
    return (
      <GardenSetup
        garden={garden}
        onSaved={(saved) => {
          setGarden(saved)
          setEditing(false)
        }}
        onCancel={() => setEditing(false)}
      />
    )

  return (
    <>
      <Section
        title={garden.name}
        description={
          <span className="flex items-center gap-1">
            <MapPin className="size-4 shrink-0" aria-hidden />
            {garden.latitude.toFixed(2)}, {garden.longitude.toFixed(2)}
          </span>
        }
        action={user.role === 'owner' && <IconButton icon={Pencil} label={t('Edit garden')} onClick={() => setEditing(true)} />}
      />
      <Tabs
        label={t('Garden')}
        value={tab}
        onChange={go}
        tabs={[
          { value: 'plan', label: t('Plan') },
          { value: 'plant', label: t('Plant') },
          { value: 'calendar', label: t('Calendar') },
          { value: 'plantings', label: t('Plantings') },
        ]}
      />
      <div hidden={tab !== 'plan'} className="flex flex-col gap-4">
        <LayoutEditor key={planRev} suggested={recs?.now ?? []} request={request} onChange={() => setRev((r) => r + 1)} />
      </div>
      {tab === 'plant' && (
        <Recommendations
          data={recs}
          error={recsError}
          retry={loadRecs}
          onPlant={(r) => {
            setRequest({ ...r })
            go('plan')
          }}
        />
      )}
      {tab === 'calendar' && <CalendarTab />}
      {tab === 'plantings' && <Plantings key={rev} onBedChange={() => setPlanRev((r) => r + 1)} />}
    </>
  )
}
