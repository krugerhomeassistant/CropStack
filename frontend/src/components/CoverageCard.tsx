import { Minus, Plus } from 'lucide-react'
import type { Coverage } from '../api'
import { N_, t } from '../i18n'
import { IconButton } from './ui'

const GROUPS: [string, string][] = [
  ['leafy', N_('Leafy greens')],
  ['fruiting', N_('Fruiting vegetables')],
  ['root', N_('Roots and tubers')],
  ['brassica', N_('Brassicas')],
  ['legume', N_('Beans and peas')],
  ['squash', N_('Squash family')],
  ['allium', N_('Onion family')],
  ['herb', N_('Herbs')],
]

/** The head count the plan is sized for. Only an owner sees the buttons; everyone else sees the number. */
export function PeopleStepper({ people, canChange, onPeople }: { people: number; canChange: boolean; onPeople: (n: number) => void }) {
  return (
    <div className="flex items-center justify-between gap-2">
      <p className="font-semibold">{t('Feeds {n} people', { n: people })}</p>
      {canChange && (
        <div className="flex items-center">
          <IconButton icon={Minus} label={t('Fewer people')} disabled={people <= 1} onClick={() => onPeople(people - 1)} />
          <IconButton icon={Plus} label={t('More people')} disabled={people >= 20} onClick={() => onPeople(people + 1)} />
        </div>
      )}
    </div>
  )
}

/** How much of the household's year the drafted plan covers, by food group. */
export default function CoverageCard({ coverage, people, canChange, onPeople }: { coverage: Coverage; people: number; canChange: boolean; onPeople: (n: number) => void }) {
  const pct = Math.round(coverage.overall * 100)
  return (
    <div className="flex flex-col gap-3 rounded-[var(--radius-row)] border border-line p-3">
      <PeopleStepper people={people} canChange={canChange} onPeople={onPeople} />
      <p className="text-sm">{t('{pct}% of what your household eats', { pct })}</p>
      <ul className="flex flex-col divide-y divide-line">
        {GROUPS.map(([key, label]) => {
          const g = coverage.groups[key]
          if (!g) return null
          const share = Math.round(g.covered * 100)
          return (
            <li key={key} className="grid grid-cols-[8.5rem_1fr_3rem] items-center gap-3 py-2 text-sm">
              <div className="min-w-0">
                <p>{t(label)}</p>
                {g.weeks_short.length > 0 && <p className="text-xs text-muted">{t('{n} weeks short', { n: g.weeks_short.length })}</p>}
              </div>
              <div className="h-2 overflow-hidden rounded-full bg-sunken" aria-hidden>
                <div className="h-full rounded-full bg-leaf" style={{ width: `${share}%` }} />
              </div>
              <p className="text-right font-semibold tabular-nums">{t('{pct}%', { pct: share })}</p>
            </li>
          )
        })}
      </ul>
      {coverage.best_change && (
        <p className="text-sm text-muted">
          {t('Adding about {m2} m² of bed would raise this by {pct} points.', { m2: coverage.best_change.m2, pct: Math.round(coverage.best_change.gain * 100) })}
        </p>
      )}
    </div>
  )
}
