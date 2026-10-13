import { useEffect, useState } from 'react'
import { MapContainer, Marker, Polygon, Popup, TileLayer, useMap } from 'react-leaflet'
import L, { type LatLngExpression } from 'leaflet'
import 'leaflet/dist/leaflet.css'
import { api, type Bed, type Garden } from '../api'
import { t } from '../i18n'
import { ErrorMessage, Section, Skeleton } from './ui'

const METRES_PER_DEG_LAT = 111_320
const toLatLng = (garden: Garden, x: number, y: number): [number, number] => [
 garden.latitude + y / METRES_PER_DEG_LAT,
 garden.longitude + x / (METRES_PER_DEG_LAT * Math.cos((garden.latitude * Math.PI) / 180)),
]
const fromLatLng = (garden: Garden, lat: number, lon: number): { x: number; y: number } => ({
 x: (lon - garden.longitude) * METRES_PER_DEG_LAT * Math.cos((garden.latitude * Math.PI) / 180),
 y: (lat - garden.latitude) * METRES_PER_DEG_LAT,
})
const centre = (garden: Garden, bed: Bed) => toLatLng(garden, bed.x + bed.width / 2, bed.y + bed.length / 2)
const corners = (garden: Garden, bed: Bed): LatLngExpression[] => [
 toLatLng(garden, bed.x, bed.y),
 toLatLng(garden, bed.x + bed.width, bed.y),
 toLatLng(garden, bed.x + bed.width, bed.y + bed.length),
 toLatLng(garden, bed.x, bed.y + bed.length),
]

function FitGarden({ garden, beds }: { garden: Garden; beds: Bed[] }) {
 const map = useMap()
 useEffect(() => {
 if (beds.length) map.fitBounds(L.latLngBounds(beds.flatMap((b) => corners(garden, b) as [number, number][])), { padding: [24, 24] })
 else map.setView([garden.latitude, garden.longitude], 20)
 }, [garden, beds, map])
 return null
}

export default function GardenMap({ garden, canEdit }: { garden: Garden; canEdit: boolean }) {

 const [beds, setBeds] = useState<Bed[] | null>(null)
 const [error, setError] = useState('')
 const [saving, setSaving] = useState<number | null>(null)
 const [origin, setOrigin] = useState<[number, number]>(() => {
 const saved = localStorage.getItem(`cropstack-map-origin-${garden.id}`)
 if (saved) {
 try { const parsed = JSON.parse(saved) as [number, number]; if (parsed.length === 2) return parsed } catch { /* use garden coordinates */ }
 }
 return [garden.latitude, garden.longitude]
 })
 useEffect(() => { api.beds().then(setBeds, (e) => setError(e instanceof Error ? e.message : t('Failed to load'))) }, [])
 if (error) return <ErrorMessage>{error}</ErrorMessage>
 if (!beds) return <Skeleton className="h-72" />
 const alignedGarden = { ...garden, latitude: origin[0], longitude: origin[1] }
 const mapCentre: LatLngExpression = origin
 return (
 <Section title={t('Garden map')} description={t('Drag the origin pin to align the plan, then drag individual beds into place. The grid editor below remains precise.') }>
 <div className="relative z-0 h-[22rem] overflow-hidden rounded-[var(--radius-section)] border border-line">
 <MapContainer center={mapCentre} zoom={20} scrollWheelZoom className="h-full w-full">
 <TileLayer attribution="&copy; OpenStreetMap contributors &copy; CARTO" url="https://{s}.basemaps.cartocdn.com/light_all/{z}/{x}/{y}{r}.png" />
 <FitGarden garden={alignedGarden} beds={beds} />
 <Marker position={origin} draggable={canEdit} eventHandlers={canEdit ? { dragend: (event) => { const p = event.target.getLatLng(); const next: [number, number] = [p.lat, p.lng]; setOrigin(next); localStorage.setItem(`cropstack-map-origin-${garden.id}`, JSON.stringify(next)) } } : undefined}>
 <Popup>{t('Garden origin — drag this to align the bed plan')}</Popup>
 </Marker>
 {beds.map((bed) => {
 const pos = centre(alignedGarden, bed)
 return (
 <span key={bed.id}>
 <Polygon positions={corners(alignedGarden, bed)} pathOptions={{ color: bed.id === saving ? '#b58a32' : '#4f795b', fillOpacity: 0.28 }}>
 <Popup>{bed.name} · {bed.width} × {bed.length} m</Popup>
 </Polygon>
 <Marker
 position={pos}
 draggable={canEdit}
 eventHandlers={canEdit ? {
 dragstart: () => setSaving(bed.id),
 dragend: (event) => {
 const point = event.target.getLatLng()
 const next = fromLatLng(garden, point.lat, point.lng)
 const x = Math.max(0, Math.round((next.x - bed.width / 2) * 10) / 10)
 const y = Math.max(0, Math.round((next.y - bed.length / 2) * 10) / 10)
 api.updateBed(bed.id, { x, y }).then(() => { setBeds((current) => current ? current.map((b) => b.id === bed.id ? { ...b, x, y } : b) : null); setSaving(null) }, (e) => { setError(e instanceof Error ? e.message : t('Failed to save')); setSaving(null) })
 },
 } : undefined}
 >
 <Popup>{bed.name}{saving === bed.id ? ` · ${t('Saving…')}` : ''}</Popup>
 </Marker>
 </span>
 )
 })}
 </MapContainer>
 </div>
 </Section>
 )
}
