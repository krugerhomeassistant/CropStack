import { useEffect, useState } from 'react'
import { api, type AiConfig, type AiProvider } from '../api'
import { t } from '../i18n'
import { Button, ErrorMessage, Field, Section } from './ui'

const PROVIDERS: { value: AiProvider; label: string }[] = [
  { value: 'ollama', label: 'Ollama (runs on your own server)' },
  { value: 'openai', label: 'OpenAI or compatible' },
  { value: 'anthropic', label: 'Anthropic (Claude)' },
]

/** Settings → AI co-pilot (owners): which service answers questions in Ask, and its key. The key is never shown again. */
export default function AiSettings() {
  const [config, setConfig] = useState<AiConfig | null>(null)
  const [provider, setProvider] = useState<AiProvider>('ollama')
  const [baseUrl, setBaseUrl] = useState('')
  const [model, setModel] = useState('')
  const [key, setKey] = useState('')
  const [message, setMessage] = useState('')
  const [error, setError] = useState('')

  const show = (c: AiConfig) => {
    setConfig(c)
    if (c.provider) {
      setProvider(c.provider)
      setBaseUrl(c.base_url)
      setModel(c.model)
    }
    setKey('')
  }
  useEffect(() => {
    api.ai().then(show, (e) => setError(e instanceof Error ? e.message : t('Failed to load')))
  }, [])

  const run = (work: Promise<unknown>, done: string) => {
    setError('')
    setMessage('')
    work.then(() => setMessage(done), (e) => setError(e instanceof Error ? e.message : t('Something went wrong')))
  }

  if (!config) return error ? <ErrorMessage>{error}</ErrorMessage> : null
  return (
    <Section
      title={t('AI co-pilot')}
      description={t('Optional. Questions in Ask go to the service you choose here; nothing is sent until someone asks.')}
    >
      {error && <ErrorMessage>{error}</ErrorMessage>}
      <form
        className="flex flex-col gap-3"
        onSubmit={(e) => {
          e.preventDefault()
          run(api.saveAi({ provider, base_url: baseUrl, model, api_key: key || null }).then(show), t('Saved'))
        }}
      >
        <Field label={t('Service')}>
          <select className="input" value={provider} onChange={(e) => setProvider(e.target.value as AiProvider)}>
            {PROVIDERS.map((p) => (
              <option key={p.value} value={p.value}>
                {t(p.label)}
              </option>
            ))}
          </select>
        </Field>
        <Field label={t('Address')} hint={t('Leave empty to use {url}', { url: config.default_urls[provider] })}>
          <input className="input" type="url" value={baseUrl} onChange={(e) => setBaseUrl(e.target.value)} />
        </Field>
        <Field label={t('Model')}>
          <input className="input" required maxLength={100} value={model} onChange={(e) => setModel(e.target.value)} />
        </Field>
        <Field
          label={t('API key')}
          hint={config.has_key ? t('A key is saved. Type a new one to replace it.') : t('Not needed for Ollama.')}
        >
          <input
            className="input"
            type="password"
            autoComplete="off"
            value={key}
            onChange={(e) => setKey(e.target.value)}
          />
        </Field>
        <div className="flex flex-wrap gap-2">
          <Button type="submit">{t('Save')}</Button>
          {config.configured && (
            <>
              <Button type="button" variant="secondary" onClick={() => run(api.testAi(), t('The service answered'))}>
                {t('Test')}
              </Button>
              {config.has_key && (
                <Button
                  type="button"
                  variant="secondary"
                  onClick={() => run(api.saveAi({ provider, base_url: baseUrl, model, api_key: '' }).then(show), t('Key removed'))}
                >
                  {t('Remove key')}
                </Button>
              )}
              <Button type="button" variant="ghost" onClick={() => run(api.clearAi().then(show), t('AI turned off'))}>
                {t('Turn off')}
              </Button>
            </>
          )}
        </div>
        {message && <p role="status" className="text-sm font-semibold text-leaf">{message}</p>}
      </form>
    </Section>
  )
}
