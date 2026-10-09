import { useState } from 'react'
import { LayoutGrid, MapPin, Pencil } from 'lucide-react'
import { EmptyState, IconButton, PageHeader, Section } from '../components/ui'
import { t } from '../i18n'
import { useApp } from '../state'
import Plantings from '../components/Plantings'
import GardenSetup from './GardenSetup'

export default function GardenPage() {
  const { user, garden, setGarden } = useApp()
  const [editing, setEditing] = useState(false)

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
      <Plantings />
      {/* shortcut: placeholder until beds and the layout editor exist (PLAN Phase 8). */}
      <Section title={t('Beds')}>
        <EmptyState icon={LayoutGrid} title={t('No beds yet')}>
          {t('Beds, containers and rows go here, drawn to scale in the layout editor. It arrives with the garden planner.')}
        </EmptyState>
      </Section>
    </>
  )
}
