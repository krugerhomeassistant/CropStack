/** The flat icon for a crop (`src/icons/crops/<slug>.svg`), sized to the surrounding text. Falls back to a seedling. */
const URLS = import.meta.glob<string>('../icons/crops/*.svg', { eager: true, query: '?url', import: 'default' })

export const cropIconUrl = (crop: string) => URLS[`../icons/crops/${crop}.svg`] ?? URLS['../icons/crops/_seedling.svg']

/** For HTML. Inside an `<svg>`, draw `<image href={cropIconUrl(crop)} />` instead. */
export function CropIcon({ crop }: { crop: string }) {
  return <img src={cropIconUrl(crop)} alt="" draggable={false} className="inline-block size-[1.15em] align-[-0.2em]" />
}
