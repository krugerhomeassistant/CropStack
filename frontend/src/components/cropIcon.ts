/** A little picture for each crop, so beds and lists can be read at a glance. Falls back to a seedling. */
const ICONS: Record<string, string> = {
  tomato: '🍅', carrot: '🥕', lettuce: '🥬', kale: '🥬', 'swiss-chard': '🥬', spinach: '🥬', cabbage: '🥬', rocket: '🥬',
  'mustard-greens': '🥬', 'pak-choi': '🥬', endive: '🥬', broccoli: '🥦', cauliflower: '🥦', 'brussels-sprouts': '🥦',
  onion: '🧅', shallot: '🧅', leek: '🧅', chives: '🧅', garlic: '🧄', 'sweet-corn': '🌽', cucumber: '🥒', zucchini: '🥒',
  eggplant: '🍆', 'sweet-pepper': '🫑', chilli: '🌶️', potato: '🥔', 'sweet-potato': '🍠', 'jerusalem-artichoke': '🥔',
  strawberry: '🍓', melon: '🍈', watermelon: '🍉', pumpkin: '🎃', pea: '🫛', 'green-bean': '🫛', 'broad-bean': '🫛',
  'runner-bean': '🫛', beetroot: '🟣', radish: '🔴', turnip: '⚪', swede: '⚪', parsnip: '🥕', celery: '🌿', celeriac: '🌿',
  parsley: '🌿', basil: '🌿', coriander: '🌿', dill: '🌿', thyme: '🌿', sage: '🌿', rosemary: '🌿', oregano: '🌿', mint: '🌿',
  fennel: '🌿', asparagus: '🌱', rhubarb: '🌱', okra: '🌱', kohlrabi: '🟢', 'globe-artichoke': '🌱', horseradish: '🌱', watercress: '🌿',
}
export const cropIcon = (slug: string): string => ICONS[slug] ?? '🌱'
