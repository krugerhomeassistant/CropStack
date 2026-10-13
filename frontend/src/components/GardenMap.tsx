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
 useEffect(() => { api.beds().then(setBeds, (e) => setError(e instanceof Error ? e.message : t('Failed to load'))) }, [])
 if (error) return <ErrorMessage>{error}</ErrorMessage>
 if (!beds) return <Skeleton className="h-72" />
 const mapCentre: LatLngExpression = [garden.latitude, garden.longitude]
 return (
 <Section title={t('Garden map')} description={t('Drag a bed marker to place it on the map. The plan below remains the precise metre-grid editor.') }>
 <div className="relative z-0 h-[22rem] overflow-hidden rounded-[var(--radius-section)] border border-line">
 <MapContainer center={mapCentre} zoom={20} scrollWheelZoom className="h-full w-full">
 <TileLayer attribution="&copy; OpenStreetMap contributors" url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png" />
 <FitGarden garden={garden} beds={beds} />
 {beds.map((bed) => {
 const pos = centre(garden, bed)
 return (
 <span key={bed.id}>
 <Polygon positions={corners(garden, bed)} pathOptions={{ color: bed.id === saving ? '#b58a32' : '#4f795b', fillOpacity: 0.28 }}>
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
