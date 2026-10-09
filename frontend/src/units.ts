/** Values are stored in SI (°C, mm, m); these convert for display per the person's units preference. */
export type Units = 'metric' | 'imperial'

export const tempValue = (c: number, units: Units) => (units === 'imperial' ? (c * 9) / 5 + 32 : c)
export const tempUnit = (units: Units) => (units === 'imperial' ? '°F' : '°C')
export const temp = (c: number, units: Units, digits = 0) => `${tempValue(c, units).toFixed(digits)} ${tempUnit(units)}`

export const rainValue = (mm: number, units: Units) => (units === 'imperial' ? mm / 25.4 : mm)
export const rainUnit = (units: Units) => (units === 'imperial' ? 'in' : 'mm')
export const rain = (mm: number, units: Units) =>
  `${rainValue(mm, units).toFixed(units === 'imperial' ? 1 : 0)} ${rainUnit(units)}`

export const length = (m: number, units: Units) =>
  units === 'imperial' ? `${Math.round(m * 3.28084)} ft` : `${Math.round(m)} m`

export const speed = (kmh: number, units: Units) =>
  units === 'imperial' ? `${Math.round(kmh / 1.609)} mph` : `${Math.round(kmh)} km/h`

/** Plant sizes and spacing (stored in cm). */
export const cm = (value: number, units: Units) =>
  units === 'imperial' ? `${Math.round(value / 2.54)} in` : `${Math.round(value)} cm`

/** Short distances such as root depth (stored in m), one decimal. */
export const metres = (value: number, units: Units) =>
  units === 'imperial' ? `${(value * 3.28084).toFixed(1)} ft` : `${value.toFixed(1)} m`
