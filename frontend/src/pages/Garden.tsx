import { useState } from 'react'
import { MapPin, Pencil } from 'lucide-react'
import { IconButton, PageHeader, Section } from '../components/ui'
import { t } from '../i18n'
import { useApp } from '../state'
import Recommendations from '../components/Recommendations'
import LayoutEditor from '../components/LayoutEditor'
import Plantings from '../components/Plantings'
import GardenSetup from './GardenSetup'

export default function GardenPage() {
  const { user, garden, setGarden } = useApp()
  const [editing, setEditing] = useState(false)
  const [rev, setRev] = useState(0) // bumped when the plan changes so the plantings list reloads
  const [planRev, setPlanRev] = useState(0) // and the other way round

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
      <PageHeader title={t('Garden')} />
      <Section
        title={garden.name}
        description={
          <span className="flex items-center gap-1">
            <MapPin className="size-4 shrink-0" aria-hidden />
            {garden.latitude.toFixed(4)}, {garden.longitude.toFixed(4)}
            {garden.postal_code && `, ${garden.postal_code}`}
          </span>
        }
        action={
          user.role === 'owner' && <IconButton icon={Pencil} label={t('Edit garden')} onClick={() => setEditing(true)} />
        }
      />
      <Recommendations reload={rev + planRev} onChange={() => setRev((r) => r + 1)} />
      <LayoutEditor key={planRev} onChange={() => setRev((r) => r + 1)} />
      <Plantings key={rev} onBedChange={() => setPlanRev((r) => r + 1)} />
    </>
  )
}
