import { useState } from 'react'
import { MapPin, Pencil } from 'lucide-react'
import { t } from '../i18n'
import { useApp } from '../state'
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
      <h1 className="text-2xl font-extrabold">{t('Garden')}</h1>
      <section className="card flex flex-col gap-2">
        <div className="flex items-start justify-between">
          <h2 className="text-xl font-extrabold">{garden.name}</h2>
          {user.role === 'owner' && (
            <button className="text-muted" onClick={() => setEditing(true)} aria-label={t('Edit garden')}>
              <Pencil className="size-5" aria-hidden />
            </button>
          )}
        </div>
        <p className="flex items-center gap-1 text-sm text-muted">
          <MapPin className="size-4" aria-hidden />
          {garden.latitude.toFixed(4)}, {garden.longitude.toFixed(4)}
          {garden.postal_code && ` · ${garden.postal_code}`}
        </p>
      </section>
      <section className="card text-sm text-muted">
        {t('Beds, plantings and the layout editor will live here.')}
      </section>
    </>
  )
}
