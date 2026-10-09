import { useEffect, useState } from 'react'
import { Sprout } from 'lucide-react'

type Health = { status: string; version: string }

export default function App() {
  const [health, setHealth] = useState<Health | null>(null)
  const [error, setError] = useState(false)

  useEffect(() => {
    fetch('/api/health')
      .then((r) => (r.ok ? r.json() : Promise.reject(r.status)))
      .then(setHealth)
      .catch(() => setError(true))
  }, [])

  return (
    <main className="mx-auto flex min-h-dvh max-w-md flex-col items-center justify-center gap-4 px-6 text-center">
      <Sprout className="size-14 text-leaf" aria-hidden />
      <h1 className="text-3xl font-extrabold">CropStack</h1>
      <p className="text-muted">From seed to storehouse.</p>
      <p className="text-sm text-muted" role="status">
        {error ? 'Server unreachable' : health ? `Server ${health.status} · v${health.version}` : 'Connecting…'}
      </p>
    </main>
  )
}
