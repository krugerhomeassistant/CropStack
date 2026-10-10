import { useEffect, useRef, useState } from 'react'
import { Link } from 'react-router'
import { Sparkles } from 'lucide-react'
import { api, type AiConfig, type Turn } from '../api'
import { t } from '../i18n'
import { useApp } from '../state'
import { Button, EmptyState, ErrorMessage, PageHeader, Section } from '../components/ui'

/** Ask the garden co-pilot: the model sees the garden's place, soil, plantings and open jobs, and can only advise. */
export default function Ask() {
  const { user } = useApp()
  const [config, setConfig] = useState<AiConfig | null>(null)
  const [turns, setTurns] = useState<Turn[]>([])
  const [text, setText] = useState('')
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState('')
  const end = useRef<HTMLDivElement>(null)

  useEffect(() => {
    api.ai().then(setConfig, (e) => setError(e instanceof Error ? e.message : t('Failed to load')))
  }, [])
  useEffect(() => end.current?.scrollIntoView?.({ block: 'nearest' }), [turns, busy])

  async function send() {
    const next: Turn[] = [...turns, { role: 'user', content: text.trim() }]
    setTurns(next)
    setText('')
    setBusy(true)
    setError('')
    try {
      const { reply } = await api.askAi(next.slice(-20))
      setTurns([...next, { role: 'assistant', content: reply }])
    } catch (e) {
      setError(e instanceof Error ? e.message : t('Something went wrong'))
    } finally {
      setBusy(false)
    }
  }

  return (
    <>
      <PageHeader title={t('Ask')} subtitle={t('Questions about your garden, answered from what CropStack knows about it.')} back />
      {error && <ErrorMessage>{error}</ErrorMessage>}
      {config && !config.configured ? (
        <EmptyState icon={Sparkles} title={t('The AI co-pilot is off')}>
          {user.role === 'owner' ? (
            <Link to="/settings" className="font-semibold underline">
              {t('Choose a service and add a key in Settings')}
            </Link>
          ) : (
            t('An owner can turn it on in Settings.')
          )}
        </EmptyState>
      ) : (
        <Section title={t('Conversation')}>
          <ul className="flex flex-col gap-3 text-sm" aria-live="polite">
            {turns.map((m, i) => (
              <li key={i} className={m.role === 'user' ? 'self-end rounded-[var(--radius-row)] bg-leaf/15 p-3' : 'whitespace-pre-wrap'}>
                {m.content}
              </li>
            ))}
            {busy && <li className="text-muted">{t('Thinking…')}</li>}
          </ul>
          <div ref={end} />
          {user.role !== 'viewer' && (
            <form
              className="flex gap-2"
              onSubmit={(e) => {
                e.preventDefault()
                if (text.trim() && !busy) send()
              }}
            >
              <input
                className="input flex-1"
                aria-label={t('Your question')}
                maxLength={4000}
                placeholder={t('My tomatoes are yellowing after three days of rain. What should I do?')}
                value={text}
                onChange={(e) => setText(e.target.value)}
              />
              <Button type="submit" disabled={busy || !text.trim()}>
                {t('Ask')}
              </Button>
            </form>
          )}
        </Section>
      )}
    </>
  )
}
