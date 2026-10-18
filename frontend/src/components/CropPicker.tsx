import { useState } from 'react'
import type { CropSummary } from '../api'
import { t } from '../i18n'
import { CropIcon } from './CropIcon'

export const label = (c: CropSummary) => c.names.en?.[0] ?? c.slug

/** Tick any number of crops. Used for "what do you want to grow" and "which seed do you have". */
export default function CropPicker({ crops, chosen, onChange }: { crops: CropSummary[]; chosen: Set<string>; onChange: (s: Set<string>) => void }) {
  const [q, setQ] = useState('')
  const shown = crops.filter((c) => label(c).toLowerCase().includes(q.trim().toLowerCase()))
  const toggle = (slug: string) => {
    const next = new Set(chosen)
    if (!next.delete(slug)) next.add(slug)
    onChange(next)
  }
  return (
    <div className="flex flex-col gap-3">
      <input className="input" type="search" placeholder={t('Search crops')} value={q} onChange={(e) => setQ(e.target.value)} />
      <div className="flex flex-wrap gap-2">
        {shown.map((c) => (
          <button
            key={c.slug}
            type="button"
            aria-pressed={chosen.has(c.slug)}
            onClick={() => toggle(c.slug)}
            className={`rounded-full border px-3 py-1.5 text-sm ${chosen.has(c.slug) ? 'border-accent bg-accent/15 font-semibold' : 'border-line'}`}
          >
            <CropIcon crop={c.slug} /> {label(c)}
          </button>
        ))}
      </div>
      <p className="text-sm text-muted">{t('{n} chosen', { n: chosen.size })}</p>
    </div>
  )
}
