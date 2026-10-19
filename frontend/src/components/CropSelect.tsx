import { useState } from 'react'
import { Check, ChevronDown, X } from 'lucide-react'
import type { CropSummary } from '../api'
import { t } from '../i18n'
import { CropIcon } from './CropIcon'
import { label } from './CropPicker'

/** A selector box for several crops: the chosen ones show as icon tags, the list keeps each crop's icon and filters as you type. */
export default function CropSelect({ crops, chosen, onChange }: { crops: CropSummary[]; chosen: string[]; onChange: (s: string[]) => void }) {
  const [open, setOpen] = useState(false)
  const [q, setQ] = useState('')
  const shown = crops.filter((c) => label(c).toLowerCase().includes(q.trim().toLowerCase()))
  const toggle = (slug: string) => onChange(chosen.includes(slug) ? chosen.filter((x) => x !== slug) : [...chosen, slug])
  const name = (slug: string) => label(crops.find((c) => c.slug === slug) ?? ({ slug, names: {} } as CropSummary))
  return (
    <div className="flex flex-col gap-2">
      <div className="flex flex-wrap gap-2">
        {chosen.map((slug) => (
          <button key={slug} type="button" aria-label={t('Remove {crop}', { crop: name(slug) })} onClick={() => toggle(slug)} className="flex items-center gap-1 rounded-full border border-accent bg-accent/15 px-3 py-1.5 text-sm font-semibold">
            <CropIcon crop={slug} /> {name(slug)} <X className="size-4" aria-hidden />
          </button>
        ))}
      </div>
      <button type="button" aria-haspopup="listbox" aria-expanded={open} onClick={() => setOpen(!open)} className="input flex items-center justify-between text-left">
        {chosen.length ? t('{n} chosen', { n: chosen.length }) : t('Choose crops…')}
        <ChevronDown className="size-4" aria-hidden />
      </button>
      {open && (
        <div className="rounded-xl border border-line bg-surface">
          <input className="input m-2 w-[calc(100%-1rem)]" type="search" aria-label={t('Search crops')} placeholder={t('Search crops')} value={q} onChange={(e) => setQ(e.target.value)} />
          <ul role="listbox" aria-multiselectable aria-label={t('Crops')} className="max-h-64 overflow-y-auto">
            {shown.map((c) => (
              <li key={c.slug} role="option" aria-selected={chosen.includes(c.slug)}>
                <button type="button" onClick={() => toggle(c.slug)} className="flex min-h-11 w-full items-center gap-2 px-3 text-left">
                  <CropIcon crop={c.slug} /> <span className="grow">{label(c)}</span>
                  {chosen.includes(c.slug) && <Check className="size-4 text-accent" aria-hidden />}
                </button>
              </li>
            ))}
          </ul>
        </div>
      )}
    </div>
  )
}
