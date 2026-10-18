import { useState } from 'react'
import { api, type Bed, type CropSummary, type PlanItem } from '../api'
import { t } from '../i18n'
import CropPicker from './CropPicker'
import { Button, ErrorMessage } from './ui'

/** Tick crops; the server lays them out in this bed at real size, around what grows there. Preview, then plant. */
export default function ArrangePanel({ bed, crops, preview, onPreview, onChange }: {
  bed: Bed
  crops: CropSummary[]
  preview: PlanItem[]
  onPreview: (items: PlanItem[]) => void
  onChange: () => void
}) {
  const [open, setOpen] = useState(false)
  const [chosen, setChosen] = useState<Set<string>>(new Set())
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState('')
  const run = async (job: () => Promise<void>) => {
    setBusy(true)
    setError('')
    try {
      await job()
    } catch (e) {
      setError(e instanceof Error ? e.message : t('Failed to save'))
    } finally {
      setBusy(false)
    }
  }
  const close = () => { setOpen(false); onPreview([]) }
  if (!open) return <Button variant="secondary" onClick={() => setOpen(true)}>{t('Arrange crops')}</Button>
  return (
    <div className="flex flex-col gap-3 rounded-[var(--radius-row)] bg-sunken p-3">
      <p className="text-sm">{t('Pick the crops. They are laid out for you at their own spacing, around what already grows here.')}</p>
      <CropPicker crops={crops} chosen={chosen} onChange={(s) => { setChosen(s); onPreview([]) }} />
      <div className="flex flex-wrap gap-2">
        <Button disabled={busy || chosen.size === 0} onClick={() => run(async () => onPreview((await api.yearPlan({ bed: bed.id, crops: [...chosen] })).items))}>
          {t('Preview')}
        </Button>
        {preview.length > 0 && (
          <Button disabled={busy} onClick={() => run(async () => {
            for (const i of preview)
              await api.addPlanting({ crop: i.crop, method: i.method, start_date: i.start_date, set_out_date: i.set_out_date, bed_id: i.bed_id, cells: i.cells, spots: i.spots, location: '', notes: '' })
            close()
            onChange()
          })}>
            {t('Plant {n} groups', { n: preview.length })}
          </Button>
        )}
        <Button variant="ghost" onClick={close}>{t('Cancel')}</Button>
      </div>
      {error && <ErrorMessage>{error}</ErrorMessage>}
    </div>
  )
}
