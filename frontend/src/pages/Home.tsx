import { LogOut, MapPin, Pencil, Sprout } from 'lucide-react'
import type { Garden, User } from '../api'
import ClimateCard from '../components/ClimateCard'

type Props = { user: User; garden: Garden; onEdit: () => void; onLogout: () => void }

export default function Home({ user, garden, onEdit, onLogout }: Props) {
  return (
    <main className="mx-auto flex min-h-dvh max-w-md flex-col gap-6 px-6 py-10">
      <header className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <Sprout className="size-7 text-leaf" aria-hidden />
          <span className="text-xl font-extrabold">CropStack</span>
        </div>
        <button className="flex items-center gap-1 text-sm text-muted" onClick={onLogout}>
          <LogOut className="size-4" aria-hidden /> Log out
        </button>
      </header>

      <p className="text-muted">Hi {user.display_name || user.username}.</p>

      <section className="card flex flex-col gap-2">
        <div className="flex items-start justify-between">
          <h1 className="text-2xl font-extrabold">{garden.name}</h1>
          <button className="text-muted" onClick={onEdit} aria-label="Edit garden">
            <Pencil className="size-5" aria-hidden />
          </button>
        </div>
        <p className="flex items-center gap-1 text-sm text-muted">
          <MapPin className="size-4" aria-hidden />
          {garden.latitude.toFixed(4)}, {garden.longitude.toFixed(4)}
          {garden.postal_code && ` · ${garden.postal_code}`}
        </p>
      </section>

      <ClimateCard gardenKey={`${garden.latitude},${garden.longitude},${garden.frost_probability}`} />

      <section className="card text-sm text-muted">Your planting calendar will appear here in a coming update.</section>
    </main>
  )
}
