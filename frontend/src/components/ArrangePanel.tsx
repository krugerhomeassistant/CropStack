import { useEffect, useRef, useState } from 'react'
import { api, type Arrangement, type Bed, type CropSummary } from '../api'
import { t } from '../i18n'
import CropSelect from './CropSelect'
import { CropIcon } from './CropIcon'
import { Button, ErrorMessage, Field } from './ui'

export type Area = [number, number, number, number] | null
export type Ghost = { crop: string; spots: [number, number, number, number][] }
type Mode = 'whole' | 'section' | 'number'

/** Pick crops, say how much of the bed they get (all of it, a section drawn on the bed, or a number of plants), and
 *  see them laid out at real size before planting. The section and the numbers follow each other. */
export default function ArrangePanel({ bed, crops, on, area, onArea, onOpen, onPreview, onChange }: {
  bed: Bed
  crops: CropSummary[]
  on: string
  area: Area
  onArea: (a: Area) => void
  onOpen: (open: boolean) => void
  onPreview: (items: Ghost[]) => void
  onChange: () => void
}) {
  const [open, setOpen] = useState(false)
  const [chosen, setChosen] = useState<string[]>([])
  const [mode, setMode] = useState<Mode>('whole')
  const [amounts, setAmounts] = useState<Record<string, string>>({})
  const [how, setHow] = useState('mixed')
  const [result, setResult] = useState<Arrangement | null>(null)
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState('')
  const grown = useRef('') // the section the server grew, so only a section drawn by hand resets the numbers

  const set = (o: boolean) => { setOpen(o); onOpen(o); if (!o) { onPreview([]); onArea(null); setResult(null) } }
  const choose = (m: Mode) => { setMode(m); setAmounts({}); onArea(null) }
  useEffect(() => {
    if (JSON.stringify(area) !== grown.current) setAmounts({}) // drawn by hand: the numbers show what the section holds
  }, [area])
  const sent = JSON.stringify([chosen, amounts, area, how, on, mode])
  useEffect(() => {
    if (!open || chosen.length === 0) { setResult(null); onPreview([]); return }
    const timer = setTimeout(() => {
      api.arrangeBed(bed.id, {
        crops: chosen.map((crop) => ({ crop, amount: mode !== 'whole' && Number(amounts[crop]) > 0 ? Number(amounts[crop]) : undefined })),
        area: mode === 'whole' ? null : area,
        how,
        start_date: on,
      }).then((r) => {
        setResult(r)
        onPreview(r.items)
        if (area && JSON.stringify(r.area) !== JSON.stringify(area)) { grown.current = JSON.stringify(r.area); onArea(r.area) }
      }, (e) => setError(e instanceof Error ? e.message : t('Failed to save')))
    }, 250)
    return () => clearTimeout(timer)
  }, [sent]) // eslint-disable-line react-hooks/exhaustive-deps

  if (!open) return <Button variant="secondary" onClick={() => set(true)}>{t('Arrange crops')}</Button>
  const companions = result?.companions.filter((c) => !chosen.includes(c.crop)) ?? []
  const today = new Date().toISOString().slice(0, 10)
  return (
    <div className="flex flex-col gap-3 rounded-[var(--radius-row)] bg-sunken p-3">
      <CropSelect crops={crops} chosen={chosen} onChange={setChosen} />
      {companions.length > 0 && (
        <div className="flex flex-col gap-1">
          <p className="text-sm text-muted">{t('Grow well beside these')}</p>
          <div className="-mx-1 flex gap-2 overflow-x-auto px-1">
            {companions.map((c) => (
              <button key={c.crop} type="button" onClick={() => setChosen([...chosen, c.crop])} className="shrink-0 rounded-full border border-line px-3 py-1.5 text-sm">
                + <CropIcon crop={c.crop} /> {c.name}
              </button>
            ))}
          </div>
        </div>
      )}
      {chosen.length > 0 && (
        <>
          <div className="grid grid-cols-3 gap-2" role="group" aria-label={t('How much of the bed')}>
            {([['whole', t('Whole bed')], ['section', t('A section')], ['number', t('A number')]] as const).map(([m, name]) => (
              <button key={m} type="button" aria-pressed={mode === m} onClick={() => choose(m)} className={`min-h-11 rounded-xl border-2 px-2 text-sm font-semibold ${mode === m ? 'border-leaf bg-leaf/15' : 'border-line bg-surface'}`}>
                {name}
              </button>
            ))}
          </div>
          {mode === 'section' && <p className="text-sm text-muted">{area ? t('Drag on the bed to draw it again.') : t('Drag across the bed to draw the section.')}</p>}
          {chosen.length > 1 && (
            <Field label={t('Mixed as')}>
              <select className="input" value={how} onChange={(e) => setHow(e.target.value)}>
                <option value="mixed">{t('Scattered')}</option>
                <option value="columns">{t('Alternating columns')}</option>
                <option value="rows">{t('Alternating rows')}</option>
              </select>
            </Field>
          )}
          <ul className="flex flex-col gap-2" aria-label={t('Plants to plant')}>
            {result?.items.map((i) => (
              <li key={i.crop} className="flex items-center justify-between gap-2 text-sm">
                <span className="flex items-center gap-2 font-semibold"><CropIcon crop={i.crop} /> {i.name}</span>
                {mode === 'whole' ? (
                  <span>{i.amount}×</span>
                ) : (
                  <label className="flex items-center gap-2">
                    <span className="text-muted">{t('of {n} fit', { n: i.capacity })}</span>
                    <input className="input w-20" type="number" min={1} aria-label={t('Plants of {crop}', { crop: i.name })} value={amounts[i.crop] ?? String(i.amount)} onChange={(e) => setAmounts({ ...amounts, [i.crop]: e.target.value })} />
                  </label>
                )}
              </li>
            ))}
          </ul>
        </>
      )}
      <div className="flex flex-wrap gap-2">
        {result && result.items.some((i) => i.amount > 0) && (
          <Button disabled={busy} onClick={async () => {
            setBusy(true)
            setError('')
            try {
              for (const i of result.items.filter((x) => x.amount > 0))
                await api.addPlanting({ crop: i.crop, method: 'direct', start_date: on, set_out_date: null, bed_id: bed.id, cells: [], spots: i.spots, in_ground: on <= today, location: '', notes: '' })
              set(false)
              onChange()
            } catch (e) {
              setError(e instanceof Error ? e.message : t('Failed to save'))
            } finally {
              setBusy(false)
            }
          }}>
            {t('Plant {n}', { n: result.items.reduce((n, i) => n + i.amount, 0) })}
          </Button>
        )}
        <Button variant="ghost" onClick={() => set(false)}>{t('Cancel')}</Button>
      </div>
      {error && <ErrorMessage>{error}</ErrorMessage>}
    </div>
  )
}
