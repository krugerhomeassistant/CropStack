import { useEffect, useState } from 'react'
import { api, type CropSummary, type Garden, type YearPlan } from '../api'
import { CropIcon } from '../components/CropIcon'
import CropPicker from '../components/CropPicker'
import { PeopleStepper } from '../components/CoverageCard'
import { Button, ErrorMessage, PageHeader } from '../components/ui'
import { t } from '../i18n'
import GardenSetup from './GardenSetup'

type Props = { garden: Garden | null; onDone: (garden: Garden) => void }
type Step = 'place' | 'people' | 'want' | 'seeds' | 'done'
const STEPS: Step[] = ['place', 'people', 'want', 'seeds', 'done']

/** First-run and "run setup again": place, people, wanted crops, seeds in hand, then a draft plan with the seed list. */
export default function Setup({ garden: start, onDone }: Props) {
  const [garden, setGarden] = useState(start)
  const [step, setStep] = useState<Step>(start ? 'people' : 'place')
  const [crops, setCrops] = useState<CropSummary[]>([])
  const [people, setPeople] = useState(2)
  const [wanted, setWanted] = useState<Set<string>>(new Set())
  const [owned, setOwned] = useState<Set<string>>(new Set())
  const [plan, setPlan] = useState<YearPlan | null>(null)
  const [error, setError] = useState('')

  useEffect(() => {
    if (!garden) return
    api.crops().then(setCrops, () => {})
    api.householdSettings().then((s) => { setPeople(s.people); setWanted(new Set(s.wanted)) }, () => {})
    api.seeds().then((s) => setOwned(new Set(s)), () => {})
  }, [garden])

  async function next() {
    setError('')
    try {
      if (step === 'people') await api.saveHouseholdSettings({ people })
      if (step === 'want') await api.saveHouseholdSettings({ wanted: [...wanted] })
      if (step === 'seeds') {
        await api.setSeeds([...owned])
        setPlan(await api.yearPlan())
      }
      setStep(STEPS[STEPS.indexOf(step) + 1])
    } catch (err) {
      setError(err instanceof Error ? err.message : t('Something went wrong'))
    }
  }

  if (step === 'place')
    return (
      <GardenSetup garden={garden} onSaved={(g) => { setGarden(g); setStep('people') }} />
    )
  const at = STEPS.indexOf(step)
  return (
    <div className="flex flex-col gap-5">
      <PageHeader title={t('Set up your garden')} subtitle={t('Step {n} of {total}', { n: at + 1, total: STEPS.length })} />
      {step === 'people' && (
        <>
          <p>{t('How many people should the garden feed? The plan sizes the beds to this.')}</p>
          <PeopleStepper people={people} canChange onPeople={setPeople} />
        </>
      )}
      {step === 'want' && (
        <>
          <p>{t('Which crops do you want to grow? The plan favours them, and still adds others where food is short.')}</p>
          <CropPicker crops={crops} chosen={wanted} onChange={setWanted} />
        </>
      )}
      {step === 'seeds' && (
        <>
          <p>{t('Which seed do you already have? The plan uses those first and lists the rest to buy.')}</p>
          <CropPicker crops={crops} chosen={owned} onChange={setOwned} />
        </>
      )}
      {step === 'done' && (
        <>
          <p>{t('Your first draft has {n} plantings. Open the Garden to review and accept them.', { n: plan?.items.length ?? 0 })}</p>
          {!!plan?.buy?.length && (
            <div>
              <h2 className="font-semibold">{t('Seeds to buy')}</h2>
              <ul className="text-sm">
                {plan.buy.map((b) => (
                  <li key={b.crop}><CropIcon crop={b.crop} /> {b.name} · {t('buy by {date}', { date: b.buy_by })}</li>
                ))}
              </ul>
            </div>
          )}
        </>
      )}
      {error && <ErrorMessage>{error}</ErrorMessage>}
      <div className="flex gap-2">
        {step !== 'done' && at > 1 && <Button variant="ghost" onClick={() => setStep(STEPS[at - 1])}>{t('Back')}</Button>}
        {step === 'done' ? (
          <Button onClick={() => garden && onDone(garden)}>{t('Open my garden')}</Button>
        ) : (
          <Button onClick={next}>{step === 'seeds' ? t('Draft my plan') : t('Next')}</Button>
        )}
      </div>
    </div>
  )
}
