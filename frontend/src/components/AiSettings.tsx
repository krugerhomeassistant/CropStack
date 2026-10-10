import { useEffect, useState } from 'react'
import { api, type AiConfig, type AiProvider } from '../api'
import { N_, t } from '../i18n'
import { Button, ErrorMessage, Field, Section } from './ui'

const PROVIDERS: { id: AiProvider; label: string; keyUrl?: string; models: string[]; note: string }[] = [
  {
    id: 'anthropic',
    label: N_('Claude (Anthropic)'),
    keyUrl: 'https://console.anthropic.com/settings/keys',
    models: ['claude-haiku-4-5-20251001', 'claude-sonnet-5-5', 'claude-opus-5-5'],
    note: N_('Haiku is fast and cheapest; Sonnet and Opus give richer answers.'),
  },
  { id: 'openai', label: N_('OpenAI'), keyUrl: 'https://platform.openai.com/api-keys', models: ['gpt-5-mini', 'gpt-5-nano', 'gpt-5'], note: '' },
  {
    id: 'openrouter',
    label: N_('OpenRouter'),
    keyUrl: 'https://openrouter.ai/keys',
    models: ['openrouter/auto'],
    note: N_('One key for many models: use any model id from openrouter.ai/models.'),
  },
  { id: 'ollama', label: N_('Ollama (your own server)'), models: ['llama3.2:3b', 'qwen3:8b'], note: N_('Runs on your own hardware. Nothing leaves your network.') },
  { id: 'custom', label: N_('Other (OpenAI-compatible)'), models: [], note: N_('LM Studio, vLLM, LiteLLM: enter its /v1 address.') },
]

/** Settings → Garden assistant (owners): which service answers questions in Ask, and its key. The key is never shown again. */
export default function AiSettings() {
  const [config, setConfig] = useState<AiConfig | null>(null)
  const [provider, setProvider] = useState<AiProvider>('anthropic')
  const [baseUrl, setBaseUrl] = useState('')
  const [model, setModel] = useState('')
  const [key, setKey] = useState('')
  const [result, setResult] = useState<{ ok: boolean; text: string } | null>(null)
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

  const fail = (e: unknown) => setError(e instanceof Error ? e.message : t('Something went wrong'))
  const body = (api_key: string | null = key.trim() || null) => ({ provider, base_url: baseUrl.trim(), model: model.trim(), api_key })
  const done = (text: string) => (c: AiConfig) => {
    show(c)
    setResult({ ok: true, text })
  }

  if (!config) return error ? <ErrorMessage>{error}</ErrorMessage> : null
  const p = PROVIDERS.find((x) => x.id === provider)!
  const defaults = config.providers[provider]
  const same = config.provider === provider
  return (
    <Section
      title={t('Garden assistant')}
      description={t('Optional. Questions in Ask go to the service you choose here; nothing is sent until someone asks.')}
    >
      {error && <ErrorMessage>{error}</ErrorMessage>}
      <form
        className="flex flex-col gap-3"
        onSubmit={(e) => {
          e.preventDefault()
          setError('')
          setResult(null)
          api.saveAi(body()).then(done(t('Saved')), fail)
        }}
      >
        <Field label={t('Service')} hint={p.note && t(p.note)}>
          <select
            className="input"
            value={provider}
            onChange={(e) => {
              setProvider(e.target.value as AiProvider)
              setBaseUrl('')
              setModel('')
              setKey('')
              setResult(null)
            }}
          >
            {PROVIDERS.map((x) => (
              <option key={x.id} value={x.id}>
                {t(x.label)}
              </option>
            ))}
          </select>
        </Field>
        {provider !== 'ollama' && (
          <Field
            label={t('API key')}
            hint={
              <>
                {same && config.has_key ? t('A key is saved{hint}. Leave blank to keep it.', { hint: config.key_hint ? ` (…${config.key_hint})` : '' }) : t('Paste your key.')}{' '}
                {p.keyUrl && (
                  <a href={p.keyUrl} target="_blank" rel="noreferrer" className="underline">
                    {t('Get a key')}
                  </a>
                )}
              </>
            }
          >
            <input className="input" type="password" autoComplete="off" value={key} onChange={(e) => setKey(e.target.value)} />
          </Field>
        )}
        <Field label={t('Model')} hint={defaults.model ? t('Leave empty to use {model}', { model: defaults.model }) : undefined}>
          <input className="input" list="ai-models" maxLength={100} value={model} onChange={(e) => setModel(e.target.value)} />
        </Field>
        <datalist id="ai-models">
          {p.models.map((m) => (
            <option key={m} value={m} />
          ))}
        </datalist>
        <Field label={t('Address')} hint={defaults.base_url ? t('Leave empty to use {url}', { url: defaults.base_url }) : t('Required, for example http://host:1234/v1')}>
          <input className="input" type="url" required={provider === 'custom'} value={baseUrl} onChange={(e) => setBaseUrl(e.target.value)} />
        </Field>
        {provider !== 'ollama' && (
          <p className="text-xs text-muted">
            {t('The key is stored only on your server. With a cloud service, the garden summary and your question are sent to it when someone uses Ask.')}
          </p>
        )}
        {result && (
          <p role="status" className={`text-sm font-semibold ${result.ok ? 'text-leaf' : 'text-harvest'}`}>
            {result.text}
          </p>
        )}
        <div className="flex flex-wrap gap-2">
          <Button type="submit">{t('Save')}</Button>
          <Button
            type="button"
            variant="secondary"
            onClick={() => {
              setError('')
              setResult(null)
              api.testAi(body()).then((r) => setResult({ ok: r.ok, text: r.ok ? t('Connected. The model replied "{reply}"', { reply: r.reply ?? '' }) : (r.error ?? '') }), fail)
            }}
          >
            {t('Test')}
          </Button>
          {config.configured && same && config.has_key && (
            <Button type="button" variant="secondary" onClick={() => api.saveAi(body('')).then(done(t('Key removed')), fail)}>
              {t('Remove key')}
            </Button>
          )}
          {config.configured && (
            <Button type="button" variant="ghost" onClick={() => api.clearAi().then(done(t('Garden assistant turned off')), fail)}>
              {t('Turn off')}
            </Button>
          )}
        </div>
      </form>
    </Section>
  )
}
