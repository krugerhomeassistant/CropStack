import { N_, t } from '../i18n'
import type { PlantingStatus } from '../api'

export const STATUS: Record<PlantingStatus, string> = {
  planned: N_('Planned'),
  sown: N_('Sown'),
  germinated: N_('Up'),
  transplanted: N_('Set out'),
  harvesting: N_('Harvesting'),
  finished: N_('Finished'),
  failed: N_('Failed'),
}

/** Pick any stage a planting is in, ahead or back; "Set out" only for plantings that are transplanted. */
export default function StatusSelect({ status, method, label, onChange }: {
  status: PlantingStatus
  method: 'direct' | 'transplant'
  label: string
  onChange: (status: PlantingStatus) => void
}) {
  return (
    <select className="input w-auto" aria-label={label} value={status} onChange={(e) => onChange(e.target.value as PlantingStatus)}>
      {(Object.keys(STATUS) as PlantingStatus[])
        .filter((s) => s !== 'transplanted' || method === 'transplant')
        .map((s) => (
          <option key={s} value={s}>
            {t(STATUS[s])}
          </option>
        ))}
    </select>
  )
}
