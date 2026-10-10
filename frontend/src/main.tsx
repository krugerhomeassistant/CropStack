import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import { BrowserRouter } from 'react-router'
import { registerSW } from 'virtual:pwa-register'
import './index.css'
import App from './App'

registerSW({ immediate: true })

// An installed app can keep showing an old bundle after the server is updated. If the server reports a newer
// version than this bundle, drop the cached copies once and reload so the new screens appear.
fetch('/api/health')
  .then((r) => r.json())
  .then(async (h: { version?: string }) => {
    if (!h.version || h.version === __APP_VERSION__ || sessionStorage.getItem('stale-reload') === h.version) return
    sessionStorage.setItem('stale-reload', h.version)
    await Promise.all((await navigator.serviceWorker?.getRegistrations?.()) ?.map((r) => r.unregister()) ?? [])
    await Promise.all((await caches.keys()).map((k) => caches.delete(k)))
    location.reload()
  })
  .catch(() => {}) // offline or storage blocked: keep what is shown


createRoot(document.getElementById('root')!).render(
  <StrictMode>
    <BrowserRouter>
      <App />
    </BrowserRouter>
  </StrictMode>,
)
